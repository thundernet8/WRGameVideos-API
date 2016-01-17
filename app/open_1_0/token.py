# coding=utf-8

from flask import request
from flask import jsonify

from . import open
from ..models import Authapp
from ..models import User
from .errors import unknown_app
from .errors import unapproved_app
from .errors import unmatched_redirect
from .errors import incorrect_openid
from .errors import incorrect_code
from .errors import incorrect_sign
from .errors import incorrect_grant_type


@open.route('/access_token', methods=['GET', 'POST'])
def get_access_token():
    """get access token for registered app
    it is only used for anonymous user, not single for a user,
    the access_token is stored in 'Authapp' table, every third app has one,
    if you need to access API data specified to a user, go visit /user_token to get one user_access_token
    """
    grant = request.args.get('grant_type')
    if not grant or grant != 'authorization_code':
        return incorrect_grant_type('grant type does not match')

    appkey = request.args.get('client_id')
    if not appkey:
        return unknown_app('unregistered application')
    authapp = Authapp.query.filter_by(app_key=appkey).first()
    if not authapp:
        return unknown_app('unregistered application')
    elif not authapp.app_status:
        return unapproved_app('unapproved application')

    redirect_url = request.args.get('redirect_url')
    stamp = request.args.get('tstamp', 0)
    sign = request.args.get('sign')
    if authapp.app_url != redirect_url[:len(authapp.app_url)]:
        return unmatched_redirect('redirect url error')
    if authapp.verify_token_request_sign(stamp, redirect_url, sign):
        return jsonify(authapp.generate_app_access_token())
    return incorrect_sign('signature error')


@open.route('/user_token')
def get_token():
    """get an access_token specified to a user and a registered third app,
    the token is stored in 'Usermeta' table, every user got one for a third app,
    if you do not access API data related to a specified user, go to visit /access_token for a general app_access_token
    """
    code = request.args.get('code')
    grant = request.args.get('grant_type')
    app_key = request.args.get('client_id')
    redirect_url = request.args.get('redirect_url')

    if not grant or grant != 'authorization_code':
        return incorrect_grant_type('grant type does not match')

    if not app_key:
        return unknown_app('unregistered application')
    authapp = Authapp.query.filter_by(app_key=app_key, app_status=1).first()
    if not authapp:
        return unknown_app('unregistered application')
    elif not authapp.app_status:
        return unapproved_app('unapproved application')

    if authapp.app_url != redirect_url[:len(authapp.app_url)]:
        return unmatched_redirect('redirect url error')

    # if getting token the first time, check the code arg
    if code:
        verify = Authapp.verify_timed_code(code)
        if verify:
            return jsonify(verify)
        return incorrect_code('authorization code error')

    # or getting token again with open_id, client_id, sign
    sign = request.args.get('sign')
    timestamp = request.args.get('tstamp')
    open_id = request.args.get('openid')
    user = User.query.filter_by(open_id=open_id).first()
    if not user:
        return incorrect_openid('open_id is incorrect')
    if authapp.verify_token_request_sign(timestamp, redirect_url, sign):
        return jsonify(user.generate_user_access_token(app_key=app_key))
    return incorrect_sign('signature error')
