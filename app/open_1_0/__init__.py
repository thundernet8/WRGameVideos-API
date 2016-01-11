from flask import Blueprint

open = Blueprint('open', __name__)

# import

from . import token, errors, login, forms
