"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import shutil
import tempfile

from OpenSSL import crypto
from mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings as _override_settings
from django.utils.six import StringIO
from django.utils.six.moves import reload_module

from django_ca import ca_settings
from django_ca.models import Certificate
from django_ca.models import CertificateAuthority
from django_ca.utils import sort_subject_dict
from django_ca.utils import get_cert_profile_kwargs
from django_ca.utils import parse_date

_fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_key(path, typ=crypto.FILETYPE_PEM):
    path = os.path.join(_fixtures_dir, path)
    with open(path, 'rb') as stream:
        return crypto.load_privatekey(typ, stream.read())


def _load_cert(path, typ=crypto.FILETYPE_PEM):
    path = os.path.join(_fixtures_dir, path)
    with open(path, 'rb') as stream:
        return crypto.load_certificate(typ, stream.read())

root_key = _load_key('root.key')
root_pubkey = _load_cert('root.pem')
child_key = _load_key('child.key')
child_pubkey = _load_cert('child.pem')
ocsp_key = _load_key('ocsp.key')
ocsp_pubkey = _load_cert('ocsp.pem')
cert1_key = _load_key('cert1.key')
cert1_pubkey = _load_cert('cert1.pem')
cert2_key = _load_key('cert2.key')
cert2_pubkey = _load_cert('cert2.pem')
cert2_key = _load_key('cert2.key')
cert2_pubkey = _load_cert('cert2.pem')


class override_settings(_override_settings):
    """Enhance override_settings to also reload django_ca.ca_settings.

    .. WARNING:: When using this class as a class decorator, the decorated class must inherit from
       :py:class:`~django_ca.tests.base.DjangoCATestCase`.
    """

    def __call__(self, test_func):
        if isinstance(test_func, type) and not issubclass(test_func, DjangoCATestCase):
            raise Exception("Only subclasses of DjangoCATestCase can use override_settings.")
        inner = super(override_settings, self).__call__(test_func)
        return inner

    def save_options(self, test_func):
        super(override_settings, self).save_options(test_func)
        reload_module(ca_settings)

    def enable(self):
        super(override_settings, self).enable()
        reload_module(ca_settings)

    def disable(self):
        super(override_settings, self).disable()
        reload_module(ca_settings)


class override_tmpcadir(override_settings):
    """Sets the CA_DIR directory to a temporary directory.

    .. NOTE: This also takes any additional settings.
    """

    def __init__(self, **kwargs):
        super(override_tmpcadir, self).__init__(**kwargs)
        self.options['CA_DIR'] = tempfile.mkdtemp()

    def disable(self):
        super(override_tmpcadir, self).disable()
        shutil.rmtree(self.options['CA_DIR'])


class DjangoCATestCase(TestCase):
    """Base class for all testcases with some enhancements."""
    fixtures_dir = _fixtures_dir

    @classmethod
    def setUpClass(cls):
        super(DjangoCATestCase, cls).setUpClass()

        if cls._overridden_settings:
            reload_module(ca_settings)

    @classmethod
    def tearDownClass(cls):
        overridden = False
        ca_dir = None
        if hasattr(cls, '_cls_overridden_context'):
            overridden = True
            ca_dir = cls._cls_overridden_context.options.get('CA_DIR')

        super(DjangoCATestCase, cls).tearDownClass()

        if overridden is True:
            reload_module(ca_settings)
            if ca_dir is not None:
                shutil.rmtree(ca_dir)

    def setUp(self):
        reload_module(ca_settings)

    def settings(self, **kwargs):
        return override_settings(**kwargs)

    def tmpcadir(self, **kwargs):
        return override_tmpcadir(**kwargs)

    def assertSubject(self, cert, expected):
        actual = cert.get_subject().get_components()
        actual = [(k.decode('utf-8'), v.decode('utf-8')) for k, v in actual]

        self.assertEqual(actual, sort_subject_dict(expected))

    @classmethod
    def init_ca(cls, **kwargs):
        """Create a new CA."""
        kwargs.setdefault('name', 'Root CA')
        kwargs.setdefault('parent', None)
        kwargs.setdefault('key_size', ca_settings.CA_MIN_KEY_SIZE)
        kwargs.setdefault('pathlen', 1)

        return CertificateAuthority.objects.init(
            key_type='RSA', algorithm='sha256', expires=720, subject={'CN': 'ca.example.com', },
            **kwargs)

    @classmethod
    def load_ca(cls, name, x509, enabled=True, parent=None, **kwargs):
        """Load a CA from one of the preloaded files."""
        path = os.path.join(_fixtures_dir, '%s.key' % name)
        ca = CertificateAuthority(name=name, private_key_path=path, enabled=enabled, parent=parent,
                                  **kwargs)
        ca.x509 = x509  # calculates serial etc
        ca.save()
        return ca

    @classmethod
    def create_csr(cls, **fields):
        # see also: https://github.com/msabramo/pyOpenSSL/blob/master/examples/certgen.py
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 1024)

        req = crypto.X509Req()

        subj = req.get_subject()
        for key, value in fields.items():
            setattr(subj, key, value)

        req.set_pubkey(pkey)
        req.sign(pkey, 'sha256')
        return pkey, req

    @classmethod
    def create_cert(cls, ca, csr, subject, san=None, **kwargs):
        cert_kwargs = get_cert_profile_kwargs()
        cert_kwargs.update(kwargs)
        cert_kwargs.setdefault('subject', {})
        cert_kwargs['subject'].update(subject)
        x509 = Certificate.objects.init(ca=ca, csr=csr, algorithm='sha256', expires=720,
                                        subjectAltName=san, **cert_kwargs)
        expires = parse_date(x509.get_notAfter().decode('utf-8'))

        cert = Certificate(ca=ca, csr=csr, expires=expires)
        cert.x509 = x509
        cert.save()
        return cert

    @classmethod
    def load_cert(cls, ca, x509):
        cert = Certificate(ca=ca, csr='none')
        cert.x509 = x509
        cert.save()
        return cert

    @classmethod
    def get_subject(cls, x509):
        return {k.decode('utf-8'): v.decode('utf-8') for k, v
                in x509.get_subject().get_components()}

    @classmethod
    def get_extensions(cls, x509):
        exts = [x509.get_extension(i) for i in range(0, x509.get_extension_count())]
        return {ext.get_short_name().decode('utf-8'): str(ext) for ext in exts}

    @classmethod
    def get_alt_names(cls, x509):
        return [n.strip() for n in cls.get_extensions(x509)['subjectAltName'].split(',')]

    def assertParserError(self, args, expected):
        """Assert that given args throw a parser error."""

        buf = StringIO()
        with self.assertRaises(SystemExit), patch('sys.stderr', buf):
            self.parser.parse_args(args)

        output = buf.getvalue()
        self.assertEqual(output, expected)
        return output

    def cmd(self, *args, **kwargs):
        kwargs.setdefault('stdout', StringIO())
        kwargs.setdefault('stderr', StringIO())
        stdin = kwargs.pop('stdin', StringIO())

        with patch('sys.stdin', stdin):
            call_command(*args, **kwargs)
        return kwargs['stdout'].getvalue(), kwargs['stderr'].getvalue()


@override_settings(CA_MIN_KEY_SIZE=512)
class DjangoCAWithCATestCase(DjangoCATestCase):
    """A test class that already has a CA predefined."""

    @classmethod
    def setUpClass(cls):
        super(DjangoCAWithCATestCase, cls).setUpClass()
        cls.ca = cls.load_ca(name='root', x509=root_pubkey)


class DjangoCAWithCSRTestCase(DjangoCAWithCATestCase):
    @classmethod
    def setUpClass(cls):
        super(DjangoCAWithCSRTestCase, cls).setUpClass()

        cls.key, cls.csr = cls.create_csr()
        cls.csr_pem = crypto.dump_certificate_request(
            crypto.FILETYPE_PEM, cls.csr).decode('utf-8').strip()


class DjangoCAWithCertTestCase(DjangoCAWithCSRTestCase):
    @classmethod
    def setUpClass(cls):
        super(DjangoCAWithCertTestCase, cls).setUpClass()
        cls.cert = cls.load_cert(cls.ca, x509=cert1_pubkey)
