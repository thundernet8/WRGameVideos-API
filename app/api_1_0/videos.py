# coding=utf-8

from flask import jsonify
from flask import request
from flask.ext.jsonpify import jsonpify

from . import api
from ..models import Video


@api.route('/videos/cate/<int:category_id>')
def get_cate_videos(category_id):
    """homepage cate videos"""
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    videos = Video.get_cate_videos_json(taxonomy_ID=category_id, limit=limit, offset=offset)
    return jsonify(videos)


@api.route('/videos/<int:video_id>')
def get_video_detial(video_id):
    """single video detail page"""
    video = Video.get_video_detail_json(video_id)
    return jsonify(video)


@api.route('/videos/recommendation')
def get_recommended_videos():
    """get recommended videos for a specified video"""
    video_id = request.args.get('video_id', 0)
    count = request.args.get('count', 10)
    callback = request.args.get('callback', 'jsonp')
    if not int(video_id):
        return jsonify(dict(status=False, videos=None))
    if not int(count):
        count = 10
    videos = Video.get_recommended_vides_json(video_id, count)
    return jsonify(videos) if callback == 'json' else jsonpify(videos)


@api.route('/videos/channel/<int:channel_id>')
def get_channel_list(channel_id):
    """a big category which includes several sub-categories could be a channel, so it's different from a simple
    category"""
    channel_data = Video.get_channel_list_json(channel_id)
    return jsonify(channel_data)


@api.route('/videos/channel/<int:channel_id>/list')
def get_channel_video_list(channel_id):
    """list videos for a channel/category, including its sub-categories, mostly called by ajax"""
    limit = request.args.get('limit', 9)
    offset = request.args.get('offset', 0)
    list_data = Video.get_channel_video_list_json(channel_id, limit, offset)
    return jsonpify(list_data)  # use jsonp for cross domain
