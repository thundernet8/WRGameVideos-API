# coding=utf-8

from flask import jsonify
from flask import request

from . import api
from ..models import Video


@api.route('/videos/cate/<int:category_id>')
def get_cate_videos(category_id):
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    videos = Video.get_cate_videos_json(taxonomy_ID=category_id, limit=limit, offset=offset)
    return jsonify(videos)
