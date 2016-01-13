# coding=utf-8

from flask import jsonify

from . import api
from ..models import Slides


@api.route('/slides')
def get_slides():
    slides = Slides.get_slides_json()
    return jsonify(slides)
