import time
import uuid

from datetime import datetime
from datetime import timedelta

from OpenSSL import crypto

from django.conf import settings
from django.db import models


class CertificateManager(models.Manager):

    def from_csr(self, csr, subjectAltNames=None, days=720):

        # get certificate information
        req = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
        subject = req.get_subject()
        cn = dict(subject.get_components())['CN']

        # get issuer cert:
        issuerKey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                           open(settings.CA_PRIVATE_KEY).read())
        issuerPub = crypto.load_certificate(crypto.FILETYPE_PEM,
                                            open(settings.CA_PUBLIC_KEY).read())

        # compute notAfter info
        expires = datetime.today() + timedelta(days=days + 1)
        expires = expires.replace(hour=0, minute=0, second=0, microsecond=0)
        notAfter = time.mktime(expires.utctimetuple())

        # create signed certificate
        cert = crypto.X509()
        cert.set_serial_number(uuid.uuid4().int)
        cert.gmtime_adj_notBefore(int(time.time()))
        cert.gmtime_adj_notAfter(int(notAfter))
        cert.set_issuer(issuerPub.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.sign(issuerKey, settings.DIGEST_ALGORITHM)

        # create database object
        obj = self.create(
            csr=csr,
            pub=crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
            cn=cn,
            expires=expires,
        )

        return obj
