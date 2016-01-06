from flask import jsonify
from app.exceptions import ValidationError
from . import api


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message, request_token=''):
    response = jsonify({'error': 'unauthorized', 'message': message, 'request_token': request_token})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def notexist(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])