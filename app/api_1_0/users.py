from flask import jsonify, url_for, request
from sqlalchemy.exc import IntegrityError
from . import api
from .errors import notexist, bad_request
from ..models import User, Video
from .. import db
import json


@api.route('/users/<int:uid>')
def get_user(uid):
    user = User.query.get(uid)
    if user is None:
        return notexist('user not exist')
    return jsonify(user.get_user_json())


@api.route('/users/<int:uid>/videos')
def get_user_videos(uid):
    user = User.query.get(uid)
    if user is None:
        return notexist('user not exist')
    return jsonify(user.get_user_videos_json())


@api.route('/users', methods=['POST'])
def add_user():
    data = json.loads(request.data)
    user_login = data.get('user_login')
    user_email = data.get('user_email')
    password = data.get('password')
    if user_login is None or password is None or user_email is None:
        return bad_request('too few arguments')
    user = User(user_login=user_login, user_email=user_email, password=password, user_displayname=data.get('user_displayname', ''), user_url=data.get('user_url', ''), role_id=1)
    db.session.add(user)
    try:
        db.session.commit()
        if user:
            return jsonify(user.get_user_json()), 201
    except IntegrityError:
        db.session.rollback()
    return bad_request('create user failed')