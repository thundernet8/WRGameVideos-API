# coding=utf-8

from flask import jsonify
from flask import request

from . import api
from ..models import Taxonomy


@api.route('/taxonomies')
def get_taxonomies_json():
    """get specified taxnonmies"""
    ids = request.args.getlist('taxonomy_id')
    if ids and len(ids) != 0:
        taxonomies = Taxonomy.get_taxonomies_json(tuple(ids))
        return jsonify(taxonomies)
    return jsonify(dict(status=False, taxonomies=None))
