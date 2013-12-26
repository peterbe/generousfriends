generousfriends
===============

Get What You Really Want


Running tests
-------------

    ./manage.py test webapp.main


Database migrations
-------------------

After you have edited `webapp/main/models.py` run:

    ./manage.py schemamigration webapp.main --auto

This will generate a new file in `webapp/main/migrations/`. Edit at
will. Then run:

    ./manage.py migrate webapp.main
