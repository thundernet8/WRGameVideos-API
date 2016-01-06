from . import open
from .errors import wrong_grant, unknown_app, unapproved_app, unmatched_redirect, incorrect_sign
from flask import url_for, render_template, redirect, request, flash, current_app, jsonify
from ..models import Authapp


@open.route('/access_token', methods=['GET', 'POST'])
def get_access_token():
    grant = request.args.get('grant_type')
    if not grant or grant != 'authorization_code':
        return wrong_grant('grant type does not match')

    appkey = request.args.get('client_id')
    if not appkey:
        return unknown_app('unregistered application')
    authapp = Authapp.query.filter_by(app_key=appkey).first()
    if not authapp:
        return unknown_app('unregistered application')
    elif not authapp.app_status:
        return unapproved_app('unapproved application')

    redirect_url = request.args.get('redirect_uri', '')
    strap = request.args.get('tstrap', 0)
    sign = request.args.get('sign', '')
    if authapp.app_url != redirect_url:
        return unmatched_redirect('redirect url error')
    if authapp.verify_token_request_sign(strap, redirect_url, sign):
        return jsonify(authapp.generate_app_access_token())
    return incorrect_sign('signature error')
