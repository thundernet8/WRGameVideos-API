from flask import g, jsonify, request, url_for
from flask.ext.httpauth import HTTPBasicAuth
from . import api
from .errors import unauthorized, forbidden
from ..models import User, AnonymousUser, Authapp
from app.open_1_0 import open

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(user_email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.user_confirmed:
        return forbidden('Unconfirmed account')

    """verify third app token"""
    if request.endpoint[:21] != 'open.get_access_token':
        if request.args.get('access_token', None) is None \
          or not Authapp.verify_app_access_token(request.args.get('access_token')):
            return unauthorized('Invalid access_token', url_for('open.get_access_token', _external=True))


@api.route('/token')
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials', url_for('api.get_token', _external=True))
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})
