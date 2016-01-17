from flask import g, jsonify, request, url_for
from . import api
from .errors import unauthorized, forbidden
from ..models import User, AnonymousUser, Authapp
from app.open_1_0 import open


@api.before_request
def before_request():
    return  # TODO clear
    """verify third app token"""
    h = request.headers
    token = h.get('X-TOKEN', None) or request.args.get('access_token')
    if token is None:
        return unauthorized('Missing access_token', url_for('open.get_access_token', _external=True))
    verify = Authapp.verify_app_access_token(token) or User.verify_user_access_token(token)
    if verify:
        g.current_authapp = verify.get('authapp')
        g.current_user = verify.get('user')
    else:
        return unauthorized('Invalid access_token', url_for('open.get_access_token', _external=True))
