import hashlib
import hmac
from datetime import datetime
import time
from flask import current_app, request, url_for
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
            if  role is None:
                role = Role(name=r)
            role.permissions = roles[r]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Taxonomy(db.Model):
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

    def __repr__(self):
        return '<Taxonomy: %r>' % self.type


class Tax_terms(db.Model):
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

    def __repr__(self):
        return '<User %r>' % self.user_login


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
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

    def generate_app_access_token(self, expiration=3600*24*30):
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
        return

    @staticmethod
    def verify_app_access_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except Exception:
            return None
        authapp = Authapp.query.filter_by(app_ID=int(data['appid']), app_key=int(data['appkey']), access_token=token).first()
        if authapp.token_expire > datetime.utcnow():
            return authapp
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

