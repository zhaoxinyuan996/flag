import json
import os
import logging
from typing import List, Tuple, Union
from app.user.dao import dao as user_dao
from app.flag.dao import dao
from flask import Blueprint, request, Response, g
from flask_jwt_extended import get_jwt_identity
from app.constants import UserClass, flag_picture_size, FileType, allow_picture_type, RespMsg, CacheTimeout
from app.flag.typedef import AddFlag, UpdateFlag, SetFlagType, \
    AddComment, AddSubComment, FlagId, GetFlagByMap, Flag, GetFlagByFlag, GetFlagByUser
from app.user.controller import get_user_info
from app.user.typedef import UserInfo
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db, redis_cli
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')

log = logging.getLogger(__name__)


# with open(os.path.join(os.path.dirname(__file__), 'location_code.json'), encoding='utf-8') as city_file:
#     location_code = json.loads(city_file.read())


def ex_user(f: Flag) -> set:
    return {'user_id'} if str(f.user_id) != get_jwt_identity() and f.hide else {}


def get_region_flag(user_id: str, get: GetFlagByMap) -> Tuple[int, List[dict]]:
    """根据定位位置获取区域内所有的点位"""
    code = dao.get_city_by_location(get.location) or 0
    if not code:
        return 0, []
    key = f'region-flag-{get.type}-{code}'
    # 缓存
    if value := redis_cli.get(key):
        return code, json.loads(value)
    else:
        value = [f.model_dump() for f in dao.get_flag_by_city(user_id, code, get)]
        redis_cli.set(key, json.dumps(value), ex=CacheTimeout.region_flag)
        return code, value


def _build(content: str) -> List[Tuple[str, bytes]]:
    """集成各种校验，返回图片"""
    pictures = request.files.getlist('pic')
    info: UserInfo = get_user_info()
    if info.user_class == UserClass.normal and len(pictures) > 1:
        return resp(RespMsg.too_large)
    elif info.user_class == UserClass.vip and len(pictures) > 9:
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
    user_id = get_jwt_identity()
    _flag = get_request_list(request.form)
    _flag['user_id'] = user_id
    _flag['pictures'] = []
    if isinstance(_flag.get('location'), str):
        _flag['location'] = json.loads(_flag['location'])
    flag = model(**_flag)

    # 获取用户级别
    user_class = get_user_info().user_class
    # 构建图片数据
    datas = _build(flag.content)
    if isinstance(datas, Response):
        return datas
    # 新建和修改走同一个函数
    with db.auto_commit():
        # 新标记要新建一个标记
        if new:
            g.error_resp = RespMsg.flag_cant_cover_others_flag
            user_dao.add_flag(user_id)
            flag.id = dao.add(flag, user_class)

        for i, data in enumerate(datas):
            suffix, b = data
            file_minio.upload(f'{flag.id}-{i}.{suffix}', FileType.flag_pic, b)
            flag.pictures.append(file_minio.get_file_url(f'{flag.id}.{suffix}', FileType.flag_pic))

        flag_id = dao.update(flag)
        if not flag_id:
            return resp(RespMsg.flag_not_exist, -1)
    return resp(RespMsg.success, flag_id=flag.id)


@bp.route('/add', methods=['post'])
@custom_jwt()
def add():
    """新增标记"""
    info = get_user_info()
    if info.allow_flag_num < 0:
        return resp(RespMsg.flag_limit)
    return _add_or_update(AddFlag, new=True)


@bp.route('/update', methods=['post'])
@custom_jwt()
def update():
    """更新标记"""
    return _add_or_update(UpdateFlag, new=False)


@bp.route('/get-flag-by-user', methods=['post'])
@args_parse(GetFlagByUser)
@custom_jwt()
def get_flag_by_user(get: GetFlagByUser):
    return resp([f.model_dump(exclude=ex_user(f)) for f in dao.get_flag_by_user(get.id, get_jwt_identity(), get)])


@bp.route('/get-flag-by-flag', methods=['post'])
@args_parse(GetFlagByFlag)
@custom_jwt()
def get_flag_by_flag(get: GetFlagByFlag):
    flag = dao.get_flag_by_flag(get.id, get_jwt_identity())
    return resp(flag.model_dump(exclude=ex_user(flag)) if flag else None)


@bp.route('/get-flag-by-map', methods=['post'])
@args_parse(GetFlagByMap)
@custom_jwt()
def get_flag_by_map(get: GetFlagByMap):
    # 10公里内4倍检索，返回详细标记
    print(get)
    if get.distance < 10000:
        get.distance *= 2
        return resp({
            'code': None,
            'detail': True,
            'flags': [f.model_dump(exclude=ex_user(f)) for f in dao.get_flag_by_map(get_jwt_identity(), get)]})
    # 10公里-100公里2.25倍检索，返回以区县层级的嵌套
    else:
        code, data = get_region_flag(get_jwt_identity(), get)
        return resp({'code': code, 'detail': False, 'flags': data})


@bp.route('/set-flag-type', methods=['post'])
@args_parse(SetFlagType)
@custom_jwt()
def set_flag_type(set_: SetFlagType):
    dao.set_flag_type(get_jwt_identity(), set_.id, set_.type)
    return resp(RespMsg.success)


@bp.route('/delete', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete(delete_: FlagId):
    """删除标记"""
    user_id = get_jwt_identity()
    with db.auto_commit():
        # 先删除，如果存在则更新用户表
        dao.delete(user_id, delete_.id) is None or user_dao.delete_flag(user_id)
    return resp(RespMsg.success)


@bp.route('/get-fav', methods=['post'])
@custom_jwt()
def get_fav():
    """我的收藏"""
    user_id = get_jwt_identity()

    return resp([i.model_dump() for i in dao.get_fav(user_id)])


@bp.route('/add-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def add_fav(delete_: FlagId):
    """删除收藏"""
    user_id = get_jwt_identity()
    dao.add_fav(user_id, delete_.id)
    return resp(RespMsg.success)


@bp.route('/delete-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_fav(delete_: FlagId):
    """删除收藏"""
    user_id = get_jwt_identity()
    dao.delete_fav(user_id, delete_.id)
    return resp(RespMsg.success)


@bp.route('/add-comment', methods=['post'])
@args_parse(AddComment)
@custom_jwt()
def add_comment(add_: AddComment):
    """添加标记"""
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
    """获取评论"""
    user_id = get_jwt_identity()
    if not dao.flag_is_open(user_id, flag.id):
        return resp(RespMsg.flag_not_exist)
    return resp([c.model_dump() for c in dao.get_comment(flag, user_id)])


@bp.route('/delete-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_comment(flag: FlagId):
    """删除评论"""
    dao.delete_comment(flag.id, get_jwt_identity())
    return resp(RespMsg.success)

# @bp.route('/get-city', methods=['post'])
# @custom_jwt()
# def get_city():
#     return resp(location_code)
