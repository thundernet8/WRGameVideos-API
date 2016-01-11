# coding=utf-8
import hashlib
import hmac
import json
from datetime import datetime
import time
from flask import current_app, request, url_for, g
from flask.ext.login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from app.exceptions import ValidationError
from app import db, login_manager
import random, string


class Permission:
    COMMENT = 0x01
    EDIT_COMMENTS = 0x02
    PUBLISH_POST = 0x04
    EDIT_POSTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'wr_roles'
    role_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False, default='Member')
    description = db.Column(db.Text)
    counts = db.Column(db.Integer, nullable=False, default=0)
    permissions = db.Column(db.Integer)
    # relations
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Member': (Permission.COMMENT),
            'Editor': (Permission.COMMENT|Permission.EDIT_COMMENTS|Permission.PUBLISH_POST|Permission.EDIT_POSTS),
            'Administrator': (0xff)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Taxonomy(db.Model):
    """a taxonomy can be a Category, a Tag or a Topic, which is used to created a set for videos"""
    __tablename__ = 'wr_taxonomy'
    taxonomy_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text)
    parent = db.Column(db.Integer, nullable=False, default=0)
    counts = db.Column(db.Integer, nullable=False, default=0)
    type = db.Column(db.String(64), nullable=False, default='Tag')  # Tag/Category/Topic
    name = db.Column(db.Text)
    thumb = db.Column(db.Text)
    # relations
    terms = db.relationship('Tax_terms', backref='taxonomy', lazy='dynamic')

    @staticmethod
    def insert_categories():
        categories = [
            {'description': '',
             'name': u'默认分类',
             'thumb': 'images/cates/default.png'
            },
            {'description': u'《英雄联盟》（简称lol）是由美国Riot Games开发，腾讯游戏运营的英雄对战网游。《英雄联盟》除了即时战略、'
                            u'团队作战外，还拥有特色的英雄、自动匹配的战网平台，包括天赋树、召唤师系统、符文等元素。',
             'name': u'英雄联盟',
             'thumb': 'images/cates/lol.png'
            },
            {'description': u'Dota以对立的两个小队展开对战，通常是5v5，正如该游戏名称所表现的，游戏目的是守护自己的远古遗迹（近卫方'
                            u'的世界之树、天灾方的冰封王座），同时摧毁对方的远古遗迹。为了到达对方的远古遗迹，一方英雄必须战胜对方的'
                            u'部队、防御建筑和英雄。《DOTA2》，是脱离了其上一代作品《DOTA》所依赖的War3的引擎，由《DOTA》的地图核心'
                            u'制作者IceFrog（冰蛙）联手美国Valve公司使用他们的Source引擎研发的、Valve运营，完美世界代理（国服），'
                            u'韩国NEXON代理（韩服）的多人联机对抗RPG',
             'name': u'Dota/Dota2',
             'thumb': 'images/cates/dota.png'
            },
            {'description': u'《炉石传说：魔兽英雄传》（Hearthstone: Heroes of Warcraft，简称炉石传说）是暴雪娱乐开发的一款集换式'
                            u'卡牌游戏, 故事背景基于魔兽争霸系列的世界观，玩家可以另行购买卡牌包',
             'name': u'炉石传说',
             'thumb': 'images/cates/hs.png'
            },
            {'description': u'《风暴英雄》 是由暴雪娱乐公司开发的一款在线多人竞技PC游戏。游戏中的英雄角色主要来自于暴雪三大经典游戏'
                            u'系列：《魔兽世界》、《暗黑破坏神》和《星际争霸》',
             'name': u'风暴英雄',
             'thumb': 'images/cates/sh.png'
            },
            {'description': u'《我的世界》(Minecraft)是一款沙盒游戏, 以让每一个玩家在三维空间中自由地创造和破坏不同种类的方块为主体。'
                            u'玩家在游戏中可以在单人或多人模式中通过摧毁或创造方块以创造精妙绝伦的建筑物和艺术，或者收集物品探索地图以完'
                            u'成游戏的主线',
             'name': u'我的世界',
             'thumb': 'images/cates/mc.png'
            },
            {'description': u'《暗黑破坏神》是1996年暴雪公司推出的一款动作RPG经典游戏系列，英文名Diablo，源于西班牙语，意为魔王、恶'
                            u'魔的意思。玩家可以在五种不同的职业中进行选择，每种职业都有一套独特的魔法和技能。玩家在冒险中可以挑战无'
                            u'以计数的恶魔、怪物和强大的BOSS，逐渐累积经验，增强能力，并且获得具有神奇力量的物品',
             'name': u'暗黑破坏神',
             'thumb': 'images/cates/d3.png'
            },
            {'description': u'《魔兽世界》（World of Warcraft）是由著名游戏公司暴雪娱乐所制作的第一款网络游戏，属于大型多人在线角色'
                            u'扮演游戏。游戏以该公司出品的即时战略游戏《魔兽争霸》的剧情为历史背景，依托魔兽争霸的历史事件和英雄人物，'
                            u'魔兽世界有着完整的历史背景时间线。玩家在魔兽世界中冒险、完成任务、新的历险、探索未知的世界、征服怪物等',
             'name': u'魔兽世界',
             'thumb': 'images/cates/wow.png'
            },
            {'description': u'《穿越火线》(Cross Fire)是一款第一人称射击游戏的网络游戏，玩家扮演控制一名持枪战斗人员，与其他玩家进'
                            u'行械斗。',
             'name': u'穿越火线',
             'thumb': 'images/cates/cf.png'
            },
        ]

        for c in categories:
            cate = Taxonomy.query.filter_by(name=c.get('name')).first()
            if cate is None:
                cate = Taxonomy(description=c.get('description'), name=c.get('name'), thumb=c.get('thumb'), type='Category')
            db.session.add(cate)
        db.session.commit()

    def __repr__(self):
        return '<Taxonomy: %r>' % self.type


class Tax_terms(db.Model):
    """instance items related to a video under taxonomy, one taxnonmy is maybe a Tag, Category or Topic Class, and it
    can include several terms"""
    __tablename__ = 'wr_terms'
    term_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_ID = db.Column(db.Integer, db.ForeignKey('wr_videos.video_ID'))
    taxonomy_ID = db.Column(db.Integer, db.ForeignKey('wr_taxonomy.taxonomy_ID'))
    # type = db.Column(db.String(64), nullable=False, default='Tag')  # Tag/Category/Topic

    def __repr__(self):
        return '<Tax_term: %r, Video_ID: %r>' % self.taxonomy.type, self.video_ID


class Usermeta(db.Model):
    __tablename__ = 'wr_usermeta'
    meta_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('wr_users.user_ID'))
    meta_key = db.Column(db.Text)
    meta_value = db.Column(db.Text)

    @staticmethod
    def get_usermeta(user_id, meta_key):
        meta = Usermeta.query.filter_by(user_ID=user_id, meta_key=meta_key).first()
        if meta:
            return meta.meta_value
        return None

    @staticmethod
    def set_usermeta(user_id, meta_key, meta_value):
        meta = Usermeta.query.filter_by(user_ID=user_id, meta_key=meta_key).first()
        if meta:
            meta.meta_value = meta_value
        else:
            meta = Usermeta(user_ID=user_id, meta_key=meta_key, meta_value=meta_value)
        db.session.add(meta)
        db.session.commit()

    def __repr__(self):
        return '<Usermeta: %r>' % self.meta_key


class User(UserMixin, db.Model):
    __tablename__ = 'wr_users'
    user_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_login = db.Column(db.Text, nullable=False, unique=True)
    user_pass = db.Column(db.Text, nullable=False)
    user_displayname = db.Column(db.Text)
    user_email = db.Column(db.Text, unique=True)
    avatar_hash = db.Column(db.Text)
    user_url = db.Column(db.Text)
    user_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_lastseen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    user_activation_key = db.Column(db.Text)
    user_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    role_id = db.Column(db.Integer, db.ForeignKey('wr_roles.role_ID'))
    open_id = db.Column(db.Text)

    # relations
    usermetas = db.relationship('Usermeta', backref='user', lazy='dynamic')
    videos = db.relationship('Video', backref='user', lazy='dynamic')
    authapps = db.relationship('Authapp', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.user_email == current_app.config['WRGV_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(name='Member').first()
        # avatar
        if self.user_email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.user_email.encode('utf-8')).hexdigest()

        # openid
        if self.open_id is None:
            self.open_id = ''.join(random.SystemRandom().choice(string.digits + string.ascii_uppercase) for _ in range(10))

    def get_id(self):
        try:
            return unicode(self.user_ID)
        except AttributeError:
            raise NotImplementedError('No `user_ID` attribute')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.user_pass = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.user_pass, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'confirm': self.user_ID})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.user_ID:
            return False
        self.user_confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'reset': self.user_ID})

    def reset_password(self, reset_token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(reset_token)
        except:
            return False
        if data.get('reset') != self.user_ID:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'reset_email': self.user_ID, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset_email') != self.user_ID:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(user_email=new_email).first() is not None:
            return False
        self.user_email = new_email
        self.avatar_hash = hashlib.md5(self.user_email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.user_lastseen = datetime.utcnow()
        db.session.add(self)

    def get_avatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.user_email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @property
    def favorite_videos(self):
        return Video.query.join(Usermeta, Usermeta.meta_value == Video.video_ID).filter(Usermeta.user_ID == self.user_ID)

    def get_user_json(self):
        json_user = {
            'uid': self.user_ID,
            'username': self.user_login,
            'user_displayname': self.user_displayname,
            'user_email': self.user_email,
            'user_since': self.user_registered,
            'user_lastseen': self.user_lastseen,
            'user_url': self.user_url,
            'avatar_hash': self.avatar_hash
        }
        return json_user

    def get_user_videos_json(self):
        s = []
        for video in self.videos:
            v = {}
            v['video_ID'] = video.video_ID
            v['video_title'] = video.video_title
            v['video_author'] = video.video_author
            v['video_cover'] = video.video_cover
            v['video_date'] = video.video_date
            v['video_description'] = video.video_description
            v['video_duration'] = video.video_duration
            v['video_from'] = video.video_from
            v['video_hd_urls'] = video.video_hd_urls
            v['video_sd_urls'] = video.video_sd_urls
            v['video_uhd_urls'] = video.video_uhd_urls
            v['video_link'] = video.video_link
            v['video_play_count'] = video.video_play_count
            v['video_score'] = video.video_score
            v['video_status'] = video.video_status
            v['video_vid'] = video.video_vid
            s.append(v)
        json_videos = {
            'uid': self.user_ID,
            'uname': self.user_login,
            'unickname': self.user_displayname,
            'videos': s
        }
        return json_videos

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.user_ID}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(int(data['id']))  # query by primary key

    def generate_user_access_token(self, expiration=3600*24*30, app_key=''):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'appkey': app_key, 'openid': self.open_id, 'expiration': expiration}).decode('ascii')
        token_expire = int(time.time()+expiration)
        token_key = 'access_token_'+str(app_key)
        token_expire_key = 'access_token_expire_'+str(app_key)
        Usermeta.set_usermeta(self.user_ID, token_key, token)
        Usermeta.set_usermeta(self.user_ID, token_expire_key, str(token_expire))
        json_token = {
            'access_token': token,
            'open_id': self.open_id,
            'expiration': expiration
        }
        return json_token

    @staticmethod
    def verify_user_access_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return None
        authapp = Authapp.query.filter_by(app_key=int(data['appkey'])).first()
        user = User.query.filter_by(open_id=data['openid']).first()
        if user is None:
            return None
        token_expire = int(Usermeta.get_usermeta(user.user_ID, 'access_token_expire'))
        if token_expire > int(time.time()):
            g.current_user = user
            g.current_authapp = authapp
            return dict(authapp=authapp, user=user)
        return None

    def __repr__(self):
        return '<User %r>' % self.user_login


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
    def get_id(self):
        return 0

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Video(db.Model):
    __tablename__ = 'wr_videos'
    video_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_author = db.Column(db.Integer, db.ForeignKey('wr_users.user_ID'))
    video_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    video_title = db.Column(db.Text)
    video_description = db.Column(db.Text)
    video_link = db.Column(db.Text)
    video_vid = db.Column(db.Text)
    video_cover = db.Column(db.Text)
    video_duration = db.Column(db.Float, nullable=False, default=0.0)
    video_sd_urls = db.Column(db.Text)
    video_hd_urls = db.Column(db.Text)
    video_uhd_urls = db.Column(db.Text)
    video_status = db.Column(db.Text, nullable=False, default='normal')  # normal/banned
    video_from = db.Column(db.Text, nullable=False, default='huya')  # huya/uuu9/17173
    video_score = db.Column(db.Float, nullable=False, default=0.0)
    video_play_count = db.Column(db.Integer, nullable=False, default=0, index=True)

    # relations
    terms = db.relationship('Tax_terms', backref='video', lazy='dynamic')

    # get video info ...

    def __repr__(self):
        return '<Video: %r>' % self.video_title


class Authapp(db.Model):
    __tablename__ = 'wr_auth_apps'
    app_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('wr_users.user_ID'))
    app_key = db.Column(db.String(32), nullable=False, unique=True)
    app_secret = db.Column(db.String(32), nullable=False)
    app_url = db.Column(db.Text, nullable=False)
    app_name = db.Column(db.String(32), nullable=False, unique=True)
    app_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    app_request_count = db.Column(db.Integer, nullable=False, default=0)
    app_level = db.Column(db.Integer, nullable=False, default=1)  # need app roles or permissions
    app_description = db.Column(db.Text)
    app_status = db.Column(db.Integer, default=0)  # 0: unapproved 1: approved
    app_icon = db.Column(db.Text)
    access_token = db.Column(db.Text)
    token_expire = db.Column(db.DateTime, default=datetime.utcfromtimestamp(time.time()+3600*24*30))  # expired in one month

    @classmethod
    def generate_app_key(cls):
        key = ''.join(random.SystemRandom().choice(string.digits) for _ in range(9))
        return key

    @classmethod
    def generate_app_secret(cls):
        secret = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(
                random.randint(10,20)))
        secret = hashlib.md5(secret).hexdigest()
        return secret

    def generate_app_access_token(self, expiration=3600*24*30*12):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({'appid': self.app_ID, 'appkey': self.app_key, 'expiration': expiration}).decode('ascii')
        self.token_expire = datetime.fromtimestamp(time.time()+expiration)
        self.access_token = token
        db.session.add(self)
        db.session.commit()
        json_token = {
            'access_token': token,
            'expiration': expiration
        }
        return json_token

    @staticmethod
    def verify_app_access_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return None
        authapp = Authapp.query.filter_by(app_ID=int(data['appid']), app_key=int(data['appkey']), access_token=token).first()
        if authapp.token_expire > datetime.utcnow():
            g.current_authapp = authapp
            g.current_user = AnonymousUser
            return dict(authapp=authapp, user=AnonymousUser)
        return None

    # user login and authorize third app, the timed code is used by third app to get access_token and user open_id
    def generate_timed_code(self, expiration=60*10, open_id=''):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        code = s.dumps({'appkey': self.app_key, 'openid': open_id, 'expiration': expiration}).decode('ascii')
        return code

    @staticmethod
    def verify_timed_code(code):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(code)
        except Exception:
            return None
        authapp = Authapp.query.filter_by(app_key=int(data['appkey']), app_status=1).first()
        user = User.query.filter_by(open_id=data['openid']).first()
        if authapp and user:
            open_id = user.open_id
            access_token = authapp.generate_app_access_token(open_id=open_id)
            return dict(access_token=access_token, open_id=open_id)
        return None

    def verify_token_request_sign(self, timestrap, redirect, sign):
        if not self.app_secret:
            return False
        t = int(time.time())
        if t-timestrap > 10:
            return False
        s = str(self.app_key)+str(timestrap)+redirect;
        h = hmac.new(self.app_secret)
        h.update(s)
        if sign == h.hexdigest():
            return True
        return False

    def __repr__(self):
        return '<Authapp: %r>' % self.app_name


class Option(db.Model):
    __tablename__ = 'wr_options'
    option_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    option_name = db.Column(db.Text)
    option_value = db.Column(db.Text)

    @staticmethod
    def get_option(option_name):
        option = Option.query.filter_by(option_name=option_name).first()
        if option:
            return option.option_value
        return None

    @staticmethod
    def set_option(option_name, option_value):
        option = Option.query.filter_by(option_name=option_name).first()
        if option:
            option.option_value = option_value
        else:
            option = Option(option_name=option_name, option_value=option_value)
        db.session.add(option)
        db.session.commit()

    def __repr__(self):
        return '<Option: %r' % self.option_name


class Slide(object):
    """a home page slide, may be a special video or an ad with link"""
    def __init__(self, **kwargs):
        self.is_ad = kwargs.get('is_ad', False)
        self.image = kwargs.get('image', '')
        self.video_id = kwargs.get('video_id', 0)
        self.title = kwargs.get('title', '')
        self.link = kwargs.get('link', '')

    def __repr__(self):
        return '<Slide: %r>' % self.title


class Slides(object):
    """home page slides"""

    def __init__(self):
        pass

    @staticmethod
    def get_slides():
        slide_list = Option.get_option('slides')
        slide_list = json.loads(slide_list)
        if not isinstance(slide_list, list):
            return None
        slides = []
        for s in slide_list:
            is_ad = s.get('is_ad', False)
            image = s.get('image', '')
            video_id = s.get('video_id', 0)
            title = s.get('title', '')
            link = s.get('link', '')
            slide = Slide(is_ad=is_ad, image=image, video_id=video_id, title=title, link=link)
            slides.append(slide)
        return slides

    @staticmethod
    def get_slides_json():
        s = []
        slide_list = Option.get_option('slides')
        slide_list = json.loads(slide_list)
        for slide in slide_list:
            dic = {
                'is_ad': slide.get('is_ad', False),
                'image': slide.get('image', ''),
                'video_id': slide.get('video_id', 0),
                'title': slide.get('title', ''),
                'link': slide.get('link', '')
            }
            s.append(dic)
        return {'slides': s}

    @staticmethod
    def set_slides(slide_list):
        if not isinstance(slide_list, list):
            return
        slide_str = json.dumps(slide_list).decode('raw_unicode_escape')
        Option.set_option('slides', slide_str)
