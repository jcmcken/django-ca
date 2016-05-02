#########
ChangeLog
#########

************************
1.0.2 (not yet released)
************************

* Move this ChangeLog from a top-level .md file to this location.

******************
1.0.1 (2016-04-27)
******************

* Officially support Python2.7 again.
* Make sure that certificate authorities cannot be removed via the web interface.

******************
1.0.0 (2016-04-27)
******************

This represents a massive new release (hence the big version jump). The project
now has a new name (**django-ca** instead of just "certificate authority") and
is now installable via pip. Since versions prior to this release probably had no users (as it
wasn't advertised anywhere), it includes several incompatible changes.

General
=======

* This project now runs under the name **django-ca** instead of just "certificate authority".
* Move the git repository is now hosted at https://github.com/mathiasertl/django-ca.
* This version now absolutely assumes Python3. Python2 is no longer supported.
* Require Django  1.8 or later.
* django-ca is now usable as a stand-alone project (via git) or as a reusable app (via pip).

Functionality
=============

* The main app was renamed from ``certificate`` to ``django_ca``. See below for how to upgrade.

manage.py interface
===================

* ``manage.py`` commands are now renamed to be more specific:

  * ``init`` -> ``init_ca``
  * ``sign`` -> ``sign_cert``
  * ``list`` -> ``list_certs``
  * ``revoke`` -> ``revoke_cert``
  * ``crl`` -> ``dump_crl``
  * ``view`` -> ``view_cert``
  * ``watch`` -> ``notify_expiring_certs``
  * ``watchers`` -> ``cert_watchers``

* Several new ``manage.py`` commands:

  * ``dump_ca`` to dump CA certificates.
  * ``dump_cert`` to dump certificates to a file.
  * ``dump_ocsp_index`` for an OCSP responder, ``dump_crl`` no longer outputs this file.
  * ``edit_ca`` to edit CA properties from the command line.
  * ``list_cas`` to list available CAs.
  * ``view_ca`` to view a CA.

* Removed the ``manage.py remove`` command.
* ``dump_{ca,cert,crl}`` can now output DER/ASN1 data to stdout.

******************
0.2.1 (2015-05-24)
******************

* Signed certificates are valid five minutes in the past to account for possible clock skew.
* Shell-scripts: Correctly pass quoted parameters to manage.py.
* Add documentation on how to test CRLs.
* Improve support for OCSP.

****************
0.2 (2015-02-08)
****************

* The ``watchers`` command now takes a serial, like any other command.
* Reworked ``view`` command for more robustness.

  * Improve output of certificate extensions.
  * Add the ``-n``/``--no-pem`` option.
  * Add the ``-e``/``--extensions`` option to print all certificate extensions.
  * Make output clearer.

* The ``sign`` command now has

  * a ``--key-usage`` option to override the ``keyUsage`` extended attribute.
  * a ``--ext-key-usage`` option to override the ``extendedKeyUsage`` extended attribute.
  * a ``--ocsp`` option to sign a certificate for an OCSP server.

* The default ``extendedKeyUsage`` is now ``serverAuth``, not ``clientAuth``.
* Update the remove command to take a serial.
* Ensure restrictive file permissions when creating a CA.
* Add requirements-dev.txt

****************
0.1 (2015-02-07)
****************

* Initial release