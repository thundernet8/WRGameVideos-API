from . import api
from .. import db
from flask import jsonify, url_for, request, redirect
import hashlib


@api.route('/')
def register_app():
    pass