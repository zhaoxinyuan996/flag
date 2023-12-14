import os
import logging
from typing import List, Tuple
from app import message
from app.flag.dao import dao
from flask import Blueprint, request, Response
from flask_jwt_extended import get_jwt_identity
from app.constants import UserLevel, flag_picture_size, FileType, allow_picture_type
from app.user.controller import get_user_level
from app.flag.typedef import AddFlag, GetFlagBy, GetFlagCountByDistance
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')

log = logging.getLogger(__name__)


def _build() -> List[Tuple[str, bytes]]:
    """集成各种校验，返回图片"""
    pictures = request.files.getlist('pic')
    level = get_user_level()
    if level == UserLevel.normal and len(pictures) > 1:
        return resp(message.too_large)
    elif level == UserLevel.vip and len(pictures) > 9:
        return resp(message.too_large)
    length = 0
    datas = []
    for p in pictures:
        _, suffix = p.filename.rsplit('.', 1)
        if suffix not in allow_picture_type:
            return resp(message.user_picture_format_error + str(allow_picture_type), -1)

        data = p.stream.read()
        length += len(data)
        if length > flag_picture_size:
            return resp(message.too_large)

        datas.append((suffix, data))
    return datas


@bp.route('/add', methods=['post'])
@custom_jwt()
def add():
    _flag = get_request_list(request.form)
    _flag['user_id'] = get_jwt_identity()
    _flag['pictures'] = []
    flag = AddFlag(**_flag)
    if len(flag.content) > 300:
        return resp(message.too_long)
    datas = _build()
    if isinstance(datas, Response):
        return datas

    with db.auto_commit():
        flag.id = dao.add(flag)

        for i, data in enumerate(datas):
            suffix, b = data
            file_minio.upload(f'{flag.id}-{i}.{suffix}', FileType.flag_pic, b, get_user_level() == UserLevel.vip)
            flag.pictures.append(file_minio.get_file_url(FileType.flag_pic, f'{flag.id}.{suffix}'))

        dao.update(flag)
    return resp(message.success, flag_id=flag.id)


@bp.route('/get-flag', methods=['post'])
@args_parse(GetFlagBy)
@custom_jwt()
def get_flag(get: GetFlagBy):
    if get.by == 'flag':
        flag = dao.get_flag_by_flag(get.key, get_jwt_identity())
        return resp(flag.model_dump() if flag else None)
    elif get.by == 'user':
        return resp([f.model_dump() for f in dao.get_flag_by_user(get.key, get_jwt_identity(), get)])
    elif get.by == 'location':
        return resp([f.model_dump() for f in dao.get_flag_by_location(get_jwt_identity(), get)])
    return resp(message.system_error)


@bp.route('/get-flag-count', methods=['post'])
@args_parse(GetFlagCountByDistance)
@custom_jwt()
def get_flag_count(get: GetFlagCountByDistance):
    return resp(dao.get_flag_by_location_count(get_jwt_identity(), get))
