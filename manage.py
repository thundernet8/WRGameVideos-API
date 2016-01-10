#!/usr/bin/env python
import os
COV = None  # coverage
if os.environ.get('WRGV_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

if os.path.exists('.env'):
    print "Importing environment vars from .env"
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app, db
from app.models import Permission, Role, Taxonomy, Tax_terms, Usermeta, User, Video, Authapp, Option, Slides
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('WRGV_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Taxonomy=Taxonomy, Tax_terms=Tax_terms, Role=Role,
                Permission=Permission, Usermeta=Usermeta, Video=Video, Authapp=Authapp, Option=Option, Slides=Slides)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.models import Role, Taxonomy, Tax_terms, Usermeta, User, Video, Option

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

    # create default categories
    Taxonomy.insert_categories()


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('WRGV_COVERAGE'):
        import sys
        os.environ['WRGV_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tests/tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


if __name__ == '__main__':
    manager.run()
