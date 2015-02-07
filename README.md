# certificate-authority

This simple project allows you to manage a local TLS certificate authority from the command line.

## Setup

First, download the project, create a virtualenv, install requirements:

```
git clone https://github.com/fsinf/certificate-authority.git
cd certificate-authority
virtualenv .
source bin/activate
pip install -r requirements.txt
```

Copy ``ca/ca/localsettings.py.example`` to ``ca/ca/localsettings.py`` and make
the necesarry adjustments. Then create the certificate authority:

```
python ca/manage.py init
```

## Configuration

The file ``ca/ca/localsettings.py.example`` contains documentation on available settings.

## Management

## License

This project is free software licensed under the [GPLv3](http://www.gnu.org/licenses/gpl.txt).