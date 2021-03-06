# -*- coding: utf-8 -*-
#
# This file is part of django-ca (https://github.com/mathiasertl/django-ca).
#
# django-ca is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# django-ca is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-ca.  If not,
# see <http://www.gnu.org/licenses/>.

import os

from datetime import datetime
from datetime import timedelta

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

from . import ca_settings
from .fields import KeyUsageField
from .fields import SubjectAltNameField
from .fields import SubjectField
from .models import Certificate
from .utils import EXTENDED_KEY_USAGE_DESC
from .utils import KEY_USAGE_DESC
from .widgets import ProfileWidget


def _initial_expires():
    return datetime.today() + timedelta(days=ca_settings.CA_DEFAULT_EXPIRES)


def _profile_choices():
    choices = [('', '----')] + [(p, p) for p in ca_settings.CA_PROFILES]
    return sorted(choices, key=lambda e: e[0])


class CreateCertificateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CreateCertificateForm, self).__init__(*args, **kwargs)

        # Set choices so we can filter out CAs where the private key does not exist locally
        field = self.fields['ca']
        field.choices = [
            (field.prepare_value(ca), field.label_from_instance(ca)) 
            for ca in self.fields['ca'].queryset.filter(enabled=True)
            if os.path.exists(ca.private_key_path)
        ]

    expires = forms.DateField(initial=_initial_expires, widget=AdminDateWidget())
    subject = SubjectField(label="Subject", required=True)
    subjectAltName = SubjectAltNameField(
        label='subjectAltName', required=False,
        help_text=_('''Coma-separated list of alternative names for the certificate.''')
    )
    profile = forms.ChoiceField(
        required=False, widget=ProfileWidget,
        help_text=_('Select a suitable profile or manually select X509 extensions below.'),
        initial=ca_settings.CA_DEFAULT_PROFILE, choices=_profile_choices)
    algorithm = forms.ChoiceField(
        label=_('Signature algorithm'), initial=ca_settings.CA_DIGEST_ALGORITHM, choices=[
            ('sha512', 'SHA-512'),
            ('sha256', 'SHA-256'),
            ('sha1', 'SHA-1 (insecure!)'),
            ('md5', 'MD5 (insecure!)'),
        ],
        help_text=_(
            'Algorithm used for signing the certificate. SHA-512 should be fine in most cases.'
        ),
    )
    keyUsage = KeyUsageField(label='keyUsage', help_text=KEY_USAGE_DESC, choices=(
        ('cRLSign', 'CRL Sign'),
        ('dataEncipherment', 'dataEncipherment'),
        ('decipherOnly', 'decipherOnly'),
        ('digitalSignature', 'Digital Signature'),
        ('encipherOnly', 'encipherOnly'),
        ('keyAgreement', 'Key Agreement'),
        ('keyCertSign', 'Certificate Sign'),
        ('keyEncipherment', 'Key Encipherment'),
        ('nonRepudiation', 'nonRepudiation'),
    ))
    extendedKeyUsage = KeyUsageField(
        label='extendedKeyUsage', help_text=EXTENDED_KEY_USAGE_DESC, choices=(
            ('serverAuth', 'SSL/TLS Web Server Authentication'),
            ('clientAuth', 'SSL/TLS Web Client Authentication'),
            ('codeSigning', 'Code signing'),
            ('emailProtection', 'E-mail Protection (S/MIME)'),
            ('timeStamping', 'Trusted Timestamping'),
            ('OCSPSigning', 'OCSP Signing'),
            ('msCodeInd', 'Microsoft Individual Code Signing (authenticode)'),
            ('msCodeCom', 'Microsoft Commercial Code Signing (authenticode)'),
            ('msCTLSign', 'Microsoft Trust List Signing'),
            ('msEFS', 'Microsoft Encrypted File System'),
        ))

    def clean_csr(self):
        data = self.cleaned_data['csr']
        lines = data.splitlines()
        if lines[0] != '-----BEGIN CERTIFICATE REQUEST-----' \
                or lines[-1] != '-----END CERTIFICATE REQUEST-----':
            raise forms.ValidationError(_("Enter a valid CSR (in PEM format)."))

        return data

    def clean_keyUsage(self):
        value, critical = self.cleaned_data['keyUsage']
        if not value:
            return None
        value = force_bytes(','.join(value))
        return critical, value

    def clean_extendedKeyUsage(self):
        value, critical = self.cleaned_data['extendedKeyUsage']
        if not value:
            return None
        value = force_bytes(','.join(value))
        return critical, value

    class Meta:
        model = Certificate
        fields = ['csr', 'watchers', 'ca', ]
        help_texts = {
            'csr': _('''The Certificate Signing Request (CSR) in PEM format. To create a new one:
<span class="shell">openssl genrsa -out hostname.key 2048
openssl req -new -key hostname.key -out hostname.csr -utf8 -batch \\
                     -subj '/CN=/hostname/emailAddress=root@hostname'
</span>'''),
        }


class RevokeCertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['revoked_reason']
