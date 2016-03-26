################################
Certificate authority management
################################

**django-ca** supports managing multiple certificate authorities as well as
child certificate authorities.

The only way to create certificate authorities is via the command line via
:doc:`manage.py commands <manage_commands>`. It is obviously most important that
the private keys of the certificate authorities are never exposed to any
attacker, and any web interface would pose an unnecessary risk.

For the same reason, the private key of a certificate authority is stored on the
filesystem and not in the database. The initial location of the private key is
configured by the :ref:`CA_DIR setting <settings-ca-dir>`. This also means that
you can run your **django-ca** on two hosts, where one host has the private key
and only uses the command line, and one with the webinterface that can still be
used to revoke certificates.

To manage certificate authorities, use the following `manage.py` commands:

======== ======================================================
Command  Description
======== ======================================================
init_ca  Create a new certificate authority.
list_cas List all currently configured certificate authorities.
edit_ca  Edit a certificate authority.
view_ca  View details of a certificate authority.
======== ======================================================

Various details of the certificate authority, mostly the x509 extensions used
when signing a certificate, can also be managed via the webinterface.

Here is a shell session that illustrates the respective manage.py commands::

   $ python manage.py init_ca --pathlen=2
      --crl-url=http://ca.example.com/crl \
      --ocsp-url=http://ocsp.ca.example.com \
      --issuer-url=http://ca.example.com/ca.crt \
      "Test CA" AT Vienna Vienna Example ExampleUnit ca.example.com
   $ python manage.py list_cas
   BD:5B:AB:5B:A2:1C:49:0D:9A:B2:AA:BC:68:ED:ED:7D - Test CA
   $ python manage.py view_ca BD:5B:AB:5B:A2:1C:49:0D:9A:B2:AA:BC:68:ED:ED:7D \
      | grep OCSP
   * OCSP URL: http://ocsp.ca.example.com
   $ python manage.py edit_ca --ocsp-url=http://new-ocsp.ca.example.com
   $ python manage.py view_ca BD:5B:AB:5B:A2:1C:49:0D:9A:B2:AA:BC:68:ED:ED:7D \
      | grep OCSP
   * OCSP URL: http://new-ocsp.ca.example.com