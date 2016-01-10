# coding=utf-8

import unittest
from app import create_app, db
from app.models import Option, Slides


class SlidesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_slides(self):
        data = [
            {'image': u'http://img1.dwstatic.com/kan/1601/316276743737/1452321795155.jpg', 'video_id': 1,
             'title': u'《全境封锁》夺回纽约 亚洲限定铁盒版宣传片', 'is_ad': False, 'link': ''},
            {'image': u'http://img2.dwstatic.com/lol/1601/316201433262/1452246293417.jpg', 'video_id': 2,
             'title': u'质量王者局 两王者带青铜大战五钻石', 'is_ad': False, 'link': ''},
            {'image': u'http://img.dwstatic.com/lol/1601/316200506782/1452245328242.jpg', 'video_id': 3,
             'title': u'疯狂TOP10 北美区至强盲僧踢爆小学生', 'is_ad': False, 'link': ''},
            {'image': u'http://img5.dwstatic.com/newgame/1601/316206802427/1452252685131.jpg', 'video_id': 0,
             'title': u'新游视玩：武侠MOBA《九阳神功》PC首测试玩', 'is_ad': True, 'link': 'http://www.taobao.com'},
            {'image': u'http://img5.dwstatic.com/mc/1512/315423848905/1451468707431.jpg', 'video_id': 4,
             'title': u'如果Herobrine设计了一款T恤', 'is_ad': False, 'link': ''},
            {'image': u'http://img1.dwstatic.com/ls/1601/316174885632/1452219701413.jpg', 'video_id': 5,
             'title': u'一可炉石史册：克尔苏加德', 'is_ad': False, 'link': ''}
        ]

        print 'Test: insert default slides'
        Slides.set_slides(data)

        print 'Test: query inserted slides data'
        slides_option = Option.get_option('slides')
        print slides_option
