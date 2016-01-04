from flask import Blueprint

auth = Blueprint('auth', __name__)

# import

from . import views, forms