#!/usr/bin/env python
# coding=utf-8
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
    Taxonomy.insert_sub_cates()


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


from HTMLParser import HTMLParser
class Li(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.classes = []
        self.images = []
        self.titles = []
        self.urls = []

        self.is_li = False

    def handle_starttag(self, tag, attrs):
        if tag == 'li' and attrs:
            self.is_li = True

        if tag == 'a' and attrs and self.is_li:
            for key, value in attrs:
                if key == 'href':
                    self.urls.append(value)
                if key == 'title':
                    self.titles.append(value)
        if tag == 'img' and attrs and self.is_li:
            #print(attrs)
            for key, value in attrs:
                if key == 'data-echo':
                    self.images.append(value)
            self.is_li = False




@manager.command
def add():
    import urllib2
    import random
    url = 'http://m.v.huya.com/lol/jiaoxue.html'
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    r = res.read()
    li = Li()
    li.feed(r)
    li.close()


    m = 0
    #print str(li.titles[0])
    l = min(len(li.titles), len(li.images), len(li.urls))
    for i in range(l):
        score = random.choice(range(20, 100))
        count = random.choice(range(1000))
        title = str(li.titles[m]).decode('utf-8')
        video = Video(video_author=1, video_link=li.urls[m], video_title=title, video_description=title,
                      video_cover=li.images[m], video_duration=2000, video_status='normal',
                      video_from='huya', video_score=score, video_star_count=count)
        term = Tax_terms(video_ID=m+243, taxonomy_ID=14)
        db.session.add(video)
        db.session.add(term)
        m += 1
    db.session.commit()



if __name__ == '__main__':
    manager.run()
