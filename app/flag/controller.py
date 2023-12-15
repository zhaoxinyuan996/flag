import os
import logging
from typing import List, Tuple, Union
from app.flag.dao import dao
from flask import Blueprint, request, Response
from flask_jwt_extended import get_jwt_identity
from app.user.controller import get_user_level
from app.constants import UserLevel, flag_picture_size, FileType, allow_picture_type, resp_msg
from app.flag.typedef import AddFlag, GetFlagBy, GetFlagCountByDistance, GetFlagByWithType, UpdateFlag, SetFlagType, \
    AddComment, AddSubComment, FlagId
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')

log = logging.getLogger(__name__)


def _build(content: str) -> List[Tuple[str, bytes]]:
    """集成各种校验，返回图片"""
    pictures = request.files.getlist('pic')
    level = get_user_level()
    if level == UserLevel.normal and len(pictures) > 1:
        return resp(resp_msg.too_large)
    elif level == UserLevel.vip and len(pictures) > 9:
        return resp(resp_msg.too_large)
    length = 0
    datas = []
    for p in pictures:
        _, suffix = p.filename.rsplit('.', 1)
        if suffix not in allow_picture_type:
            return resp(resp_msg.user_picture_format_error + str(allow_picture_type), -1)

        data = p.stream.read()
        length += len(data)
        if length > flag_picture_size:
            return resp(resp_msg.too_large)

        datas.append((suffix, data))

    if len(content) > 300:
        return resp(resp_msg.too_long)

    return datas


def _add_or_update(model: Union[type(AddFlag), type(UpdateFlag)], new: bool):
    """新增和修改"""
    _flag = get_request_list(request.form)
    _flag['user_id'] = get_jwt_identity()
    _flag['pictures'] = []
    flag = model(**_flag)

    datas = _build(flag.content)
    if isinstance(datas, Response):
        return datas

    with db.auto_commit():
        if new:
            flag.id = dao.add(flag)

        for i, data in enumerate(datas):
            suffix, b = data
            file_minio.upload(f'{flag.id}-{i}.{suffix}', FileType.flag_pic, b, get_user_level() == UserLevel.vip)
            flag.pictures.append(file_minio.get_file_url(FileType.flag_pic, f'{flag.id}.{suffix}'))

        flag_id = dao.update(flag)
        if not flag_id:
            return resp(resp_msg.flag_not_exist, -1)
    return resp(resp_msg.success, flag_id=flag.id)


@bp.route('/add', methods=['post'])
@custom_jwt()
def add():
    return _add_or_update(AddFlag, new=True)


@bp.route('/update', methods=['post'])
@custom_jwt()
def update():
    return _add_or_update(UpdateFlag, new=False)


@bp.route('/get-flag', methods=['post'])
@args_parse(GetFlagBy)
@custom_jwt()
def get_flag(get: GetFlagBy):
    if get.by == 'flag':
        flag = dao.get_flag_by_flag(get.key, get_jwt_identity())
        return resp(flag.model_dump() if flag else None)
    elif get.by == 'user':
        return resp([f.model_dump() for f in dao.get_flag_by_user(get.key, get_jwt_identity(), get)])
    return resp(resp_msg.system_error)


@bp.route('/get-flag-type', methods=['post'])
@args_parse(GetFlagByWithType)
@custom_jwt()
def get_flag_type(get: GetFlagByWithType):
    if get.by == 'location':
        return resp([f.model_dump() for f in dao.get_flag_by_location(get_jwt_identity(), get)])
    return resp(resp_msg.system_error)


@bp.route('/get-flag-count', methods=['post'])
@args_parse(GetFlagCountByDistance)
@custom_jwt()
def get_flag_count(get: GetFlagCountByDistance):
    return resp(dao.get_flag_by_location_count(get_jwt_identity(), get))


@bp.route('/set-flag-type', methods=['post'])
@args_parse(SetFlagType)
@custom_jwt()
def set_flag_type(set_: SetFlagType):
    dao.set_flag_type(get_jwt_identity(), set_.id, set_.type)
    return resp(resp_msg.success)


@bp.route('/add-comment', methods=['post'])
@args_parse(AddComment)
@custom_jwt()
def add_comment(add_: AddComment):
    dao.add_comment(add_.flag_id, get_jwt_identity(), add_.content, add_.location, None, None)
    return resp(resp_msg.success)


@bp.route('/add-sub-comment', methods=['post'])
@args_parse(AddSubComment)
@custom_jwt()
def add_sub_comment(add_: AddSubComment):
    resp_nickname = dao.get_nickname_by_comment_id(add_.ask_user_id) or ' '
    prefix = '@' + resp_nickname

    with db.auto_commit():
        root_comment_id = dao.add_comment(
            add_.flag_id, get_jwt_identity(), add_.content, add_.location, add_.root_comment_id, prefix)
        dao.add_sub_comment(root_comment_id)
    return resp(resp_msg.success)


@bp.route('/get-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def get_comment(flag: FlagId):
    user_id = get_jwt_identity()
    if not dao.flag_is_open(user_id, flag.id):
        return resp(resp_msg.flag_not_exist)
    return resp([c.model_dump() for c in dao.get_comment(flag,  user_id)])


@bp.route('/delete-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_comment(flag: FlagId):
    dao.delete_comment(flag.id ,get_jwt_identity())
    return resp(resp_msg.success)
