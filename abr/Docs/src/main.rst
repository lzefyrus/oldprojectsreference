Plataforma de provisionameto - ABR
==================================

Overview
--------

**ABR** is a system that delivers information about brazilian phone
numbers reggarding operator, state, type and portability status.

Technology
~~~~~~~~~~

GIT REPO
^^^^^^^^

https://server11.whitelabel.com.br/portabilidadenumerica/portabilidadenumerica

Dependencies
^^^^^^^^^^^^

-  SO Windows, OSX or Linux
-  Python 3.4+
-  PIP
-  Internet access for package download
-  virtualenv \ *not required, but prior*\ 
-  root access \ *only if port 80 is used*\ 

Servers
^^^^^^^

-  Flask app server: http://flask.pocoo.org/
-  Crate.io database: http://www.crate.io/

Packages - Python 3.4
^^^^^^^^^^^^^^^^^^^^^

-  alabaster
-  Babel
-  beautifulsoup4 - *HTML Parser like jQuery*
-  configobj - *Configuration file*
-  crate - *Database connector*
-  docutils
-  ecdsa
-  Flask
-  Flask-SQLAlchemy
-  gnureadline
-  itsdangerous
-  Jinja2
-  MarkupSafe
-  netstruct
-  paramiko
-  pycrypto
-  Pygments
-  pysftp
-  pytz
-  requests
-  six
-  snowballstemmer
-  Sphinx - *Documentation*
-  sphinx-rtd-theme
-  SQLAlchemy - *DB ORM*
-  Unidecode
-  urllib3
-  Werkzeug - *Http service for performance*
-  wheel
-  gunicorn

Project Structure
~~~~~~~~~~~~~~~~~

Files
^^^^^

-  abr

   -  data - ***import files folder***

      -  delta
      -  full

   -  Docs

      -  Interno - ***internal implementation***
      -  Recebido - ***received files***
      -  src - ***apidoc source files***

   -  log - ***parser and site log files***
   -  abr\_site\_parser.py - ***FLASK REST API main filed***
   -  config.ini - ***configuration file***
   -  delta\_import.py - ***delta importer with sftp download***
   -  importer.py - ***general purpose site, file and data parser and
      importer***
   -  models.py - ***database models classes***
   -  operator.sql - ***some operators insert script***
   -  readme.txt - ***readme file***
   -  requirements.txt - ***pyton dependencies via pip***
   -  tables.sql - ***table creation sql***
   -  utils.py - ***general utility file***

Instalation
~~~~~~~~~~~

with virtualenv

::

    >cd <destination folder>

    >vittualenv -p <path of python3> env_abr
    >source env_abr/bin/activate


    >git clone https://server11.whitelabel.com.br/portabilidadenumerica/portabilidadenumerica.git abr

    >cd abr
    >pip install -r requirements.txt

Configure the *config.ini* file with the paths and dadabase information

for app server run:

::

    >source env_abr/bin/activate
    >gunicorn -w 50 -b 0.0.0.0:8889 abr_site_parser.py:app

manual delta import ***this can set as a CRON JOB***

::

    >source env_abr/bin/activate
    >python delta_import.py -h
    usage: delta_import.py [-h] [-a] [-r]

    ABR delta importing

    optional arguments:
      -h, --help      show this help message and exit
      -a, --all       Run parser for all files in data folder
      -r, --run_only  Dont download new files from sftp server, overrides the -a
                      option

    EX: 
    >python delta_import.py -a (downloads files from server and runs parser for all files in the downloaded folder)
    >python delta_import.py -r (only runs parser for all files in the downloaded folder, no download)

import base data and full file \ ***ensure there is no data on
database***\ 

::

    >source env_abr/bin/activate
    >screen
    >python importer.py 

that script will take a lot of time to run, the progress can be seen on
the log files

    be aware that www.anatel.gov.br will block calls from Amazon
    servers; so the DDD table will need to be populated by hand and the
    **run\_all** value must be set to **0** in config file