# coding=utf-8
import urllib

from flask import url_for
from flask import render_template
from flask import redirect
from flask import request
from flask import g
from flask import jsonify
from flask.ext.login import current_user
from flask.ext.login import login_user

from . import open
from .errors import incorrect_sign
from .errors import incorrect_openid
from .errors import wrong_grant
from .errors import unknown_app
from .errors import unapproved_app
from .errors import unmatched_redirect
from .errors import incorrect_code
from forms import OpenLoginForm
from ..models import User
from ..models import Authapp


@open.route('/authorize', methods=['GET', 'POST'])
def open_authorize():
    """open login
    third app which has registered in this api website and got appkey&appsecret
    can use the account system to login to its own website
    """

    form = OpenLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, False)  # maybe not required
            # access_token = g.authapp.generate_app_access_token(open_id=user.open_id)

            # add openid to redirect_uri
            # add state to redirect_uri - avoid fake redirect
            # add access_token to redirect_uri

            code = g.authapp.generate_timed_code(user.open_id)
            redirect_url = request.args.get('redirect_uri') or url_for('main.index')
            redirect_url = redirect_url+'&'+urllib.urlencode({'code': code, 'state': g.state}) if r'?' in redirect_url \
                else redirect_url+'?'+urllib.urlencode({'code': code, 'state': g.state})
            return redirect(redirect_url)

    appkey = request.args.get('client_id')
    redirect_url = request.args.get('redirect_uri', '')
    strap = request.args.get('tstrap', 0)
    sign = request.args.get('sign', '')

    # state arg used for client to verify request from server
    state = request.args.get('state', '')

    # check required data in request args
    if not appkey:
        return render_template('open/authorize_error.html', msg='unregistered application')
    authapp = Authapp.query.filter_by(app_key=appkey, app_status=1).first()
    if not authapp:
        return render_template('open/authorize_error.html', msg='unregistered application')
    elif not authapp.app_status:
        return render_template('open/authorize_error.html', msg='unapproved application')

    if authapp.app_url != redirect_url[:len(authapp.app_url)]:
        return render_template('open/authorize_error.html', msg='redirect_url is missing or unmatched')
    if not authapp.verify_token_request_sign(strap, redirect_url, sign):
        return render_template('open/authorize_error.html', msg='signature error')

    g.authapp = authapp
    g.state = state

    return render_template('open/authorize.html', form=form)


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
        return wrong_grant('grant type does not match')

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
    timestrap = request.args.get('tstrap')
    open_id = request.args.get('openid')
    user = User.query.filter_by(open_id=open_id).first()
    if not user:
        return incorrect_openid('open_id is incorrect')
    if authapp.verify_token_request_sign(timestrap, redirect_url, sign):
        return jsonify(user.generate_user_access_token(app_key=app_key))
    return incorrect_sign('signature error')
