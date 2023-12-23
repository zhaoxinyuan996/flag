import json
import os
import logging
from typing import List, Tuple, Union
from app.flag.dao import dao
from flask import Blueprint, request, Response
from flask_jwt_extended import get_jwt_identity
from app.user.controller import get_user_class
from app.constants import UserClass, flag_picture_size, FileType, allow_picture_type, RespMsg
from app.flag.typedef import AddFlag, GetFlagBy, UpdateFlag, SetFlagType, \
    AddComment, AddSubComment, FlagId, GetFlagByMap, GetFlagByMapCount
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')

log = logging.getLogger(__name__)


def _build(content: str) -> List[Tuple[str, bytes]]:
    """集成各种校验，返回图片"""
    pictures = request.files.getlist('pic')
    level = get_user_class()
    if level == UserClass.normal and len(pictures) > 1:
        return resp(RespMsg.too_large)
    elif level == UserClass.vip and len(pictures) > 9:
        return resp(RespMsg.too_large)
    length = 0
    datas = []
    for p in pictures:
        _, suffix = p.filename.rsplit('.', 1)
        if suffix not in allow_picture_type:
            return resp(RespMsg.user_picture_format_error + str(allow_picture_type), -1)

        data = p.stream.read()
        length += len(data)
        if length > flag_picture_size:
            return resp(RespMsg.too_large)

        datas.append((suffix, data))

    if len(content) > 300:
        return resp(RespMsg.too_long)

    return datas


def _add_or_update(model: Union[type(AddFlag), type(UpdateFlag)], new: bool):
    """新增和修改"""
    _flag = get_request_list(request.form)
    _flag['user_id'] = get_jwt_identity()
    _flag['pictures'] = []
    if isinstance(_flag['location'], str):
        _flag['location'] = json.loads(_flag['location'])
    flag = model(**_flag)

    # 获取用户级别
    user_class: UserClass = get_user_class()

    # 构建图片数据
    datas = _build(flag.content)
    if isinstance(datas, Response):
        return datas
    # 新建和修改走同一个函数
    with db.auto_commit():
        # 新标记要新建一个标记
        if new:
            flag.id = dao.add(flag, user_class.value)

        for i, data in enumerate(datas):
            suffix, b = data
            file_minio.upload(f'{flag.id}-{i}.{suffix}', FileType.flag_pic, b, user_class == UserClass.vip)
            flag.pictures.append(file_minio.get_file_url(FileType.flag_pic, f'{flag.id}.{suffix}'))

        flag_id = dao.update(flag)
        if not flag_id:
            return resp(RespMsg.flag_not_exist, -1)
    return resp(RespMsg.success, flag_id=flag.id)


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
    if not get.by:
        return resp([f.model_dump() for f in dao.get_flag_by_user(None, get_jwt_identity(), get)])
    if get.by == 'flag':
        flag = dao.get_flag_by_flag(get.key, get_jwt_identity())
        return resp(flag.model_dump() if flag else None)
    elif get.by == 'user':
        return resp([f.model_dump() for f in dao.get_flag_by_user(get.key, get_jwt_identity(), get)])
    return resp(RespMsg.system_error)


@bp.route('/get-flag-by-map', methods=['post'])
@args_parse(GetFlagByMap)
@custom_jwt()
def get_flag_by_map(get: GetFlagByMap):
    return resp([f.model_dump() for f in dao.get_flag_by_map(get_jwt_identity(), get)])


@bp.route('/get-flag-by-map-count', methods=['post'])
@args_parse(GetFlagByMapCount)
@custom_jwt()
def get_flag_by_map_count(get: GetFlagByMapCount):
    return resp(dao.get_flag_by_map_count(get_jwt_identity(), get))


@bp.route('/set-flag-type', methods=['post'])
@args_parse(SetFlagType)
@custom_jwt()
def set_flag_type(set_: SetFlagType):
    dao.set_flag_type(get_jwt_identity(), set_.id, set_.type)
    return resp(RespMsg.success)


@bp.route('/add-comment', methods=['post'])
@args_parse(AddComment)
@custom_jwt()
def add_comment(add_: AddComment):
    user_id = get_jwt_identity()
    if not dao.flag_exist(user_id, add_.flag_id):
        return resp(RespMsg.flag_not_exist)
    dao.add_comment(add_.flag_id, user_id, add_.content, add_.location, None, None)
    return resp(RespMsg.success)


@bp.route('/add-sub-comment', methods=['post'])
@args_parse(AddSubComment)
@custom_jwt()
def add_sub_comment(add_: AddSubComment):
    user_id = get_jwt_identity()
    # 标记是否存在
    if not dao.flag_exist(user_id, add_.flag_id):
        return resp(RespMsg.comment_not_exist)

    # 这里要做一个系统通知
    # 获取用户昵称
    # 评论层级只能2层，回复评论的root_comment_id一定是null
    ask_user_nickname = dao.get_nickname_by_comment_id(user_id, add_.flag_id, add_.root_comment_id)
    if not ask_user_nickname:
        return resp(RespMsg.comment_not_exist)

    dao.add_comment(add_.flag_id, user_id, add_.content, add_.location, add_.root_comment_id, ask_user_nickname)
    return resp(RespMsg.success)


@bp.route('/get-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def get_comment(flag: FlagId):
    user_id = get_jwt_identity()
    if not dao.flag_is_open(user_id, flag.id):
        return resp(RespMsg.flag_not_exist)
    return resp([c.model_dump() for c in dao.get_comment(flag,  user_id)])


@bp.route('/delete-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_comment(flag: FlagId):
    dao.delete_comment(flag.id ,get_jwt_identity())
    return resp(RespMsg.success)
