# coding=utf-8
import urllib

from flask import url_for
from flask import render_template
from flask import redirect
from flask import request
from flask.ext.login import login_user
from flask.ext.login import current_user

from . import open
from forms import OpenLoginForm
from ..models import User
from ..models import Authapp


@open.route('/authorize', methods=['GET', 'POST'])
def open_authorize():
    """open login
    third app which has registered in this api website and got appkey&appsecret
    can use the account system to login to its own website
    """
    response_type = request.args.get('response_type')
    appkey = request.args.get('client_id')
    redirect_url = request.args.get('redirect_url', '')
    stamp = request.args.get('tstamp', 0)
    sign = request.args.get('sign', '')

    # state arg used for client to verify request from server
    state = request.args.get('state', '')

    # check required data in request args
    if response_type != 'code':
        return render_template('open/authorize_error.html', msg='incorrect response type')

    if not appkey:
        return render_template('open/authorize_error.html', msg='unregistered application')

    authapp = Authapp.query.filter_by(app_key=appkey, app_status=1).first()
    if not authapp:
        return render_template('open/authorize_error.html', msg='unregistered application')
    elif not authapp.app_status:
        return render_template('open/authorize_error.html', msg='unapproved application')

    if authapp.app_url != redirect_url[:len(authapp.app_url)]:
        return render_template('open/authorize_error.html', msg='redirect_url is missing or unmatched')

    if not authapp.verify_token_request_sign(stamp, redirect_url, sign):
        return render_template('open/authorize_error.html', msg='signature error')

    form = OpenLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, False)  # maybe not required

    if current_user.is_authenticated:
        code = authapp.generate_timed_code(open_id=current_user.open_id)
        redirect_url = request.args.get('redirect_url') or url_for('main.index')
        redirect_url = redirect_url+'&'+urllib.urlencode({'code': code, 'state': state}) if r'?' in redirect_url \
            else redirect_url+'?'+urllib.urlencode({'code': code, 'state': state})
        return redirect(redirect_url)

    return render_template('open/authorize.html', form=form)
