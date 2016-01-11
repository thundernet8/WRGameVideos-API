from flask import g, jsonify, request, url_for
from . import api
from .errors import unauthorized, forbidden
from ..models import User, AnonymousUser, Authapp
from app.open_1_0 import open


@api.before_request
def before_request():

    """verify third app token"""
    if request.endpoint[:21] != 'open.get_access_token':
        h = request.headers
        token = h.get('X-TOKEN', None) or request.args.get('access_token')
        if token is None or not Authapp.verify_app_access_token(token):
            return unauthorized('Invalid access_token', url_for('open.get_access_token', _external=True))
