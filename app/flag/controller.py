import json
import os
import logging
import pickle
from typing import List, Tuple, Union
from uuid import UUID

from app.user.dao import dao as user_dao
from app.flag.dao import dao
from flask import Blueprint, request, g
from app.constants import UserClass, flag_picture_size, FileType, allow_picture_type, RespMsg, CacheTimeout, \
    StatisticsType, AppError
from app.flag.typedef import AddFlag, UpdateFlag, SetFlagType, \
    AddComment, FlagId, GetFlagByMap, GetFlagByFlag, GetFlagByUser, CommentId, FlagSinglePictureDone, Flag
from app.user.controller import get_user_info
from app.user.typedef import User
from app.util import args_parse, resp, custom_jwt, get_request_list, PictureStorageSet, PictureStorage
from util.database import db, redis_cli
from util.up_oss import up_oss

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')

log = logging.getLogger(__name__)


# with open(os.path.join(os.path.dirname(__file__), 'location_code.json'), encoding='utf-8') as city_file:
#     location_code = json.loads(city_file.read())


def get_flag_info(flag_id: UUID) -> Flag:
    key = f'flag-info-{flag_id}'
    if value := redis_cli.get(key):
        return pickle.loads(value)
    else:
        info: Flag = dao.get_flag_info(g.user_id, flag_id)
        if not info:
            raise AppError(RespMsg.flag_not_exist)
        redis_cli.set(key, pickle.dumps(info), ex=CacheTimeout.flag_info)
        return info


def get_region_flag(user_id: UUID, get: GetFlagByMap) -> Tuple[int, List[dict]]:
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


def set_statistics(user_id: Union[UUID, List[UUID]], flag_id: UUID, key: str):
    """
    设置flag更改状态,
    后面改成每n秒同步一次？事务一致性怎么保证？操作也放进缓存再做同步？
    """
    if isinstance(user_id, (UUID, str)):
        user_id = (user_id, )
    assert getattr(StatisticsType, key)
    dao.set_statistics(flag_id, **{key: user_id})


@bp.route('/add', methods=['post'])
@args_parse(AddFlag)
@custom_jwt()
def add(flag: AddFlag):
    """新增标记"""
    info = get_user_info()
    if info.allow_flag_num < 0:
        return resp(RespMsg.flag_limit)
    # 获取用户级别
    user_id = g.user_id
    user_class = get_user_info().user_class
    # 新建标记
    g.error_resp = RespMsg.flag_cant_cover_others_flag
    with db.auto_commit():
        user_dao.add_flag(user_id)
        flag_p = dao.add(user_id, flag, user_class)
        dao.insert_statistics(flag_p.id)

    return resp(RespMsg.success, flag_id=flag_p.id)


@bp.route('/update', methods=['post'])
@args_parse(UpdateFlag)
@custom_jwt()
def update(flag: UpdateFlag):
    """更新标记"""
    flag_p = dao.update(g.user_id, flag)
    if flag_p:
        return resp(RespMsg.success, flag_id=flag_p.id, pictures=flag_p.pictures)
    return resp(RespMsg.success)


@bp.route('/single-upload-picture', methods=['post'])
@custom_jwt()
def single_upload_picture():
    """
    针对于微信小程序这种傻逼东西单次上传
    先存到redis，60s过期，然后调用single-upload-picture-done全拿出来上传
    """
    user_id = g.user_id
    flag_id = UUID(request.form['id'])
    file = request.files.get('file')
    # 鉴权
    flag_info: Flag = get_flag_info(flag_id)
    if flag_info.user_id is None:
        raise
    key = f'{user_id}-{flag_id}-file'
    # 滥用
    if redis_cli.scard(key) >= 9:
        raise
    b = file.stream.read()
    if len(b) > flag_picture_size:
        return resp(RespMsg.too_large, -1)
    storage: PictureStorage = PictureStorage(file.filename, b)
    redis_cli.sadd(key, pickle.dumps(storage))
    redis_cli.expire(key, 60)
    return resp(RespMsg.success)


@bp.route('/single-upload-picture-clear', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def single_upload_picture_clear(clear: FlagId):
    user_id = g.user_id
    flag_id = clear.id
    key = f'{user_id}-{flag_id}-file'
    redis_cli.delete(key)
    return resp(RespMsg.success)


@bp.route('/single-upload-picture-done', methods=['post'])
@args_parse(FlagSinglePictureDone)
@custom_jwt()
def single_upload_picture_done(upload: FlagSinglePictureDone):
    user_id = g.user_id
    flag_id = upload.id
    key = f'{user_id}-{flag_id}-file'

    user_info = get_user_info()

    if user_info.user_class == UserClass.vip or user_info.user_class == UserClass.hidden:
        assert len(upload.file_list) <= 9
    else:
        assert len(upload.file_list) <= 1

    old_names = dao.get_pictures(user_id, flag_id)
    if old_names is None:
        return resp(RespMsg.flag_not_exist)

    pictures: PictureStorageSet = PictureStorageSet({pickle.loads(i) for i in redis_cli.smembers(key)})
    all_pictures: List[Union[str, PictureStorage]] = []
    for url in upload.file_list:
        filename = url.rsplit('/', 1)[-1]
        if url.startswith('http://cdn') or url.startswith('https://cdn'):
            all_pictures.append(filename)
        else:
            if filename in pictures:
                all_pictures.append(pictures.pop(filename))

    # 删除旧的图片
    for name in old_names:
        if name not in all_pictures:
            up_oss.delete(FileType.flag_pic, name)

    # 构建名字
    names = [f"{up_oss.random_str()}.{flag_id}.{p.suffix}"
             if isinstance(p, PictureStorage) else p for p in all_pictures]
    # 存表
    dao.upload_pictures(user_id, flag_id, names)
    for i in range(len(all_pictures)):
        if isinstance(all_pictures[i], PictureStorage):
            # 上传
            up_oss.upload(FileType.flag_pic, names[i], all_pictures[i].data)
    redis_cli.delete(key)
    return resp(RespMsg.success)


@bp.route('/upload-pictures', methods=['post'])
@custom_jwt()
def upload_pictures():
    user_id = g.user_id
    flag_id = UUID(request.form['id'])
    pictures = get_request_list(request.files)['file']
    if not isinstance(pictures, list):
        pictures = [pictures]

    # 删除旧的图片
    old_names = dao.get_pictures(user_id, flag_id)
    if old_names is None:
        return resp(RespMsg.flag_not_exist)
    for name in old_names:
        up_oss.delete(FileType.flag_pic, name)
    # 构建名字
    names = [f"{up_oss.random_str()}.{flag_id}.{p.filename.rsplit('.', 1)[1]}" for p in pictures]
    # 存表
    dao.upload_pictures(user_id, flag_id, names)
    # 上传
    for i in range(len(pictures)):
        up_oss.upload(FileType.flag_pic, names[i], pictures[i].stream.read())

    return resp(RespMsg.success)


@bp.route('/get-flag-by-user', methods=['post'])
@args_parse(GetFlagByUser)
@custom_jwt()
def get_flag_by_user(get: GetFlagByUser):
    return resp([f.model_dump() for f in dao.get_flag_by_user(get.id, g.user_id, get)])


@bp.route('/get-flag-by-flag', methods=['post'])
@args_parse(GetFlagByFlag)
@custom_jwt()
def get_flag_by_flag(get: GetFlagByFlag):
    if flag := dao.get_flag_by_flag(g.user_id, get.id):
        return resp(flag.model_dump())
    return resp(RespMsg.flag_not_exist)


@bp.route('/get-flag-by-map', methods=['post'])
@args_parse(GetFlagByMap)
@custom_jwt()
def get_flag_by_map(get: GetFlagByMap):
    # 10公里内4倍检索，返回详细标记
    print(get)
    if get.distance < 10000:
        get.distance *= 4
        return resp({
            'code': None,
            'detail': True,
            'flags': [f.model_dump() for f in dao.get_flag_by_map(g.user_id, get)]})
    # 10公里-100公里2.25倍检索，返回以区县层级的嵌套
    else:
        code, data = get_region_flag(g.user_id, get)
        return resp({'code': code, 'detail': False, 'flags': data})


@bp.route('/set-flag-type', methods=['post'])
@args_parse(SetFlagType)
@custom_jwt()
def set_flag_type(set_: SetFlagType):
    dao.set_flag_type(g.user_id, set_.id, set_.type)
    return resp(RespMsg.success)


@bp.route('/delete', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete(delete_: FlagId):
    """删除标记"""
    user_id = g.user_id
    with db.auto_commit():
        # 先删除，如果存在则更新用户表
        if flag_pictures := dao.delete(user_id, delete_.id):
            for p in flag_pictures.pictures:
                up_oss.delete(FileType.flag_pic, p)
            # 删除用户表的计数器
            user_dao.delete_flag(user_id)
            # 删除标记统计表
            dao.delete_statistics(flag_pictures.id)
    return resp(RespMsg.success)


@bp.route('/get-fav', methods=['post'])
@custom_jwt()
def get_fav():
    """我的收藏"""
    user_id = g.user_id
    return resp([i.model_dump() for i in dao.get_fav(user_id)])


@bp.route('/add-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def add_fav(add_: FlagId):
    """添加收藏"""
    user_id = g.user_id
    with db.auto_commit():
        if flag_id := dao.add_fav(user_id, add_.id):
            set_statistics(user_id, flag_id, StatisticsType.fav_users_up)
    return resp(RespMsg.success)


@bp.route('/delete-fav', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_fav(delete_: FlagId):
    """删除收藏"""
    user_id = g.user_id
    with db.auto_commit():
        if flag_id := dao.delete_fav(user_id, delete_.id):
            set_statistics(user_id, flag_id, StatisticsType.fav_users_down)
    return resp(RespMsg.success)


@bp.route('/add-like', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def add_like(like: FlagId):
    """点赞"""
    user_id = g.user_id
    is_like = dao.is_like(user_id, like.id)
    if not is_like:
        set_statistics(user_id, like.id, StatisticsType.like_users_up)
    return resp(RespMsg.success)


@bp.route('/delete-like', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def delete_like(delete_: FlagId):
    """取消点赞"""
    user_id = g.user_id
    is_like = dao.is_like(user_id, delete_.id)
    if is_like:
        set_statistics(user_id, delete_.id, StatisticsType.like_users_down)
    return resp(RespMsg.success)


@bp.route('/add-comment', methods=['post'])
@args_parse(AddComment)
@custom_jwt()
def add_comment(add_: AddComment):
    """添加评论"""
    user_id = g.user_id
    distance = dao.get_comment_distance(user_id, add_.flag_id, add_.location)
    # 判断距离
    if distance is None:
        return resp(RespMsg.flag_not_exist)
    # 回复的用户
    if add_.parent_id:
        ask_user_nickname = dao.get_nickname_by_comment_id(user_id, add_.flag_id, add_.parent_id)
        if not ask_user_nickname:
            return resp(RespMsg.comment_not_exist)
        comment_id = dao.add_comment(user_id, add_, distance if add_.show_distance else None)
    else:
        # 根评论才计数
        with db.auto_commit():
            if comment_id := dao.add_comment(user_id, add_, distance if add_.show_distance else None):
                set_statistics(user_id, add_.flag_id, StatisticsType.comment_users_up)

    return resp(RespMsg.success, comment_id=comment_id)


# @bp.route('/add-sub-comment', methods=['post'])
# @args_parse(AddComment)
# @custom_jwt()
# def add_sub_comment(add_: AddComment):
#     user_id = g.user_id
#     # 标记是否存在
#     if not dao.flag_exist(user_id, add_.flag_id):
#         return resp(RespMsg.comment_not_exist)
#
#     # 这里要做一个系统通知
#     # 获取用户昵称
#     # 评论层级只能2层，回复评论的root_comment_id一定是null
#     ask_user_nickname = dao.get_nickname_by_comment_id(user_id, add_.flag_id, add_.root_comment_id)
#     if not ask_user_nickname:
#         return resp(RespMsg.comment_not_exist)
#
#     comment_id = dao.add_comment(
#         add_.flag_id, user_id, add_.content, add_.location, add_.root_comment_id, ask_user_nickname)
#     return resp(RespMsg.success, comment_id=comment_id)


@bp.route('/get-comment', methods=['post'])
@args_parse(FlagId)
@custom_jwt()
def get_comment(flag: FlagId):
    """获取评论"""
    user_id = g.user_id
    if not dao.flag_is_open(user_id, flag.id):
        return resp(RespMsg.flag_not_exist)
    return resp([c.model_dump() for c in dao.get_comment(user_id, flag.id)])


@bp.route('/delete-comment', methods=['post'])
@args_parse(CommentId)
@custom_jwt()
def delete_comment(comment: CommentId):
    """删除评论"""
    with db.auto_commit():
        delete_ = dao.delete_comment(g.user_id, comment.id)
        # 如果是根评论就删除计数
        if delete_ and delete_.parent_id is None:
            set_statistics(g.user_id, delete_.flag_id, StatisticsType.comment_users_down)
    return resp(RespMsg.success)

# @bp.route('/get-city', methods=['post'])
# @custom_jwt()
# def get_city():
#     return resp(location_code)
