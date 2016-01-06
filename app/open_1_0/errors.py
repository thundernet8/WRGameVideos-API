from flask import jsonify

def wrong_grant(message):
    response = jsonify({'error': 'grant_type_error', 'message': message})
    response.status_code = 200
    return response


def unknown_app(message):
    response = jsonify({'error': 'unknown_app_error', 'message': message})
    response.status_code = 200
    return response


def unapproved_app(message):
    response = jsonify({'error': 'unapproved_app_error', 'message': message})
    response.status_code = 200
    return response


def unmatched_redirect(message):
    response = jsonify({'error': 'unmatched_redirect', 'message': message})
    response.status_code = 200
    return response

def incorrect_sign(message):
    response = jsonify({'error': 'incorrect_sign', 'message': message})
    response.status_code = 200
    return response
