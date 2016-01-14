from flask import Blueprint

api = Blueprint('api', __name__)

# import

from . import auth, errors, users, authapps, slides, videos