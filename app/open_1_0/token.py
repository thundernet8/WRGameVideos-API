from . import open
from .errors import unknown_app, unapproved_app, unmatched_redirect, incorrect_sign, incorrect_grant_type
from flask import url_for, render_template, redirect, request, current_app, jsonify
from ..models import Authapp


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
