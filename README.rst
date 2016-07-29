Opwen webapp
============

.. image:: https://travis-ci.org/OPWEN/opwen-webapp.svg?branch=master
  :target: https://travis-ci.org/OPWEN/opwen-webapp

Development setup
-----------------

First, get the source code.

.. sourcecode :: sh

  git clone git@github.com:OPWEN/opwen-webapp.git

Second, install the dependencies for the package and verify your checkout by
running the tests.

.. sourcecode :: sh

  cd opwen-webapp

  virtualenv -p $(which python3) --no-site-packages virtualenv
  . virtualenv/bin/activate
  pip install -r requirements.txt

  pip install nose
  nosetests

Third, create your local database for development and seed it with some random
test data.

.. sourcecode :: sh

  touch opwen.db
  ./manage.py db upgrade
  ./manage.py db migrate
  ./manage.py dbpopulate
