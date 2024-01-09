import logging
import os
import pickle
import re
from uuid import UUID

import requests
from app.user.dao import dao
from flask import Blueprint, request, g
from app.util import resp, custom_jwt, args_parse, refresh_user, dcs_lock
from app.constants import RespMsg, allow_picture_type, user_picture_size, FileType, AppError, CacheTimeout
from app.user.typedef import SignIn, SignUp, UserId, SignWechat, SetUserinfo, UserInfo, QueryUser
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity
from common.job import DelayJob
from util.config import config
from util.database import db, redis_cli
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')
wechat_config = config['wechat-miniapp']

username_pattern = re.compile(r'^[a-zA-Z0-9_-]{4,16}$')
password_pattern = re.compile(r'.*(?=.{6,16})(?=.*\d)(?=.*[A-Z])(?=.*[a-z]).*$')

log = logging.getLogger(__name__)


def get_user_info() -> UserInfo:
    # 加一层g？
    # 加一层redis
    user_id = g.user_id
    key = f'user-info-{user_id}'
    if value := redis_cli.get(key):
        return pickle.loads(value)
    else:
        info: UserInfo = dao.get_info(user_id)
        if not info:
            raise AppError(RespMsg.user_not_exist)
        redis_cli.set(key, pickle.dumps(info), ex=CacheTimeout.user_info)
        return info


def exists_black_list(user_id: UUID, black_id: UUID) -> bool:
    return bool(dao.exist_black_list(user_id, black_id))


@bp.route('/sign-up', methods=['post'])
@args_parse(SignUp)
def sign_up(user: SignUp):
    # 密码强度，密码强度正则，最少6位，包括至少1个大写字母，1个小写字母，1个数字
    if len(user.username) > 16 or not username_pattern.match(user.username):
        return resp(RespMsg.user_sign_up_username_weak, -1)
    if len(user.password) > 16 or not password_pattern.match(user.password):
        return resp(RespMsg.user_sign_up_password_weak, -1)

    user.password = generate_password_hash(user.password, method='pbkdf2:sha256')
    user_id = dao.sign_up(user.username, user.password, user.nickname)
    return resp(RespMsg.user_sign_up_success, user_id=user_id)


@bp.route('/sign-in', methods=['post'])
@args_parse(SignIn)
def sign_in(user: SignIn):
    res = dao.sign_in(user.username)
    if not res:
        return resp(RespMsg.user_not_exist, -1)
    user_id, password = res
    if check_password_hash(password, user.password):
        access_token = create_access_token(identity=user_id)
        DelayJob.job_queue.put(refresh_user(user_id))
        return resp(RespMsg.user_sign_in_success, user_id=user_id, access_token=access_token)
    else:
        return resp(RespMsg.user_sign_in_password_error, -1)


@bp.route('/sign-up-wechat', methods=['post'])
@args_parse(SignWechat)
def sign_up_wechat(wechat: SignWechat):
    url = ("https://api.weixin.qq.com/sns/jscode2session?"
           f"appid={wechat_config['app_id']}&secret={wechat_config['app_secret']}&"
           f"js_code={wechat.code}&grant_type=authorization_code")
    res = requests.get(url)
    open_id = res.json().get('openid')
    if open_id is None:
        raise ValueError(f'wechat content: {res.json()}')

    user_id = dao.wechat_exist(open_id)
    new = False
    if user_id is None:
        new = True
        with db.auto_commit():
            user_id = dao.third_part_sigh_up_third('wechat', open_id, '')
            dao.third_part_sigh_up_user(user_id)

    access_token = create_access_token(identity=user_id)
    DelayJob.job_queue.put(refresh_user(user_id))
    return resp(RespMsg.user_sign_in_success, user_id=user_id, new=new, access_token=access_token)


# @bp.route('/refresh-jwt', methods=['post'])
# @custom_jwt()
# def refresh_jwt():
#     """更新jwt，要结合更多的redis？用户状态控制？"""
#     user_id = g.user_id
#     access_token = create_access_token(identity=user_id)
#     DelayJob.job_queue.put(refresh_user(user_id))
#     return resp(RespMsg.user_sign_in_success, access_token=access_token)


@bp.route('/user-info', methods=['post'])
@args_parse(QueryUser)
@custom_jwt()
def user_info(query: QueryUser):
    # 查看别人的信息
    user_id = g.user_id
    if query.id:
        # 判断是否在黑名单中
        if dao.exist_black_list(query.id, user_id):
            return resp(RespMsg.user_in_black_list)
        res = dao.other_user_info(query.id, user_id)
        if not res:
            return resp(RespMsg.user_not_exist)
        return resp(res.model_dump())
    # 查看自己的信息
    else:
        res = dao.user_info(user_id)
        return resp(res.model_dump())


@dcs_lock('upload-avatar')
@bp.route('/upload-avatar', methods=['post'])
@custom_jwt()
def upload_avatar():
    """设置头像"""
    user_id = g.user_id
    suffix = request.files['file'].filename.rsplit('.', 1)[1]
    if suffix not in allow_picture_type:
        return resp(RespMsg.user_picture_format_error + str(allow_picture_type), -1)
    b = request.files['file'].stream.read()
    if len(b) > user_picture_size:
        return resp(RespMsg.too_large, -1)

    # 生成文件名
    new_filename = f'{user_id}.{file_minio.random_str()}.{suffix}'
    new_url = file_minio.get_file_url(new_filename, FileType.head_pic)
    # 获取旧的图片，删除旧图片
    old_url = dao.get_avatar_url(user_id)
    file_minio.remove_object(old_url, FileType.head_pic)
    # 设置数据库，再上传
    dao.set_avatar_url(user_id, new_url)
    file_minio.upload(new_filename, FileType.head_pic, b)
    print('old:', old_url)
    print('new:', new_url)
    return resp(RespMsg.success, avatar_url=new_url)


@bp.route('/set-userinfo', methods=['post'])
@args_parse(SetUserinfo)
@custom_jwt()
def set_userinfo(set_: SetUserinfo):
    """设置用户信息，可以多个信息一起设置"""
    info = set_.model_dump()
    if not any(info.values()):
        return resp(RespMsg.success)
    # pydantic和url
    if 'avatar' in info:
        info['avatar'] = str(info['avatar'])
    dao.set_userinfo(g.user_id, info)
    return resp(RespMsg.success)


@bp.route('/follow-add', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_add(user: UserId):
    """关注"""
    if not dao.exist(user.id):
        return resp(RespMsg.user_not_exist)
    user_id = g.user_id
    if user_id == user.id:
        return resp(RespMsg.cant_follow_self, -1)
    dao.follow_add(user_id, user.id)
    return resp(RespMsg.success)


@bp.route('/follow-remove', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_remove(user: UserId):
    """取关"""
    dao.follow_remove(g.user_id, user.id)
    return resp(RespMsg.success)


@bp.route('/follow-star', methods=['post'])
@custom_jwt()
def follow_star():
    """我的关注"""
    stars = dao.follow_star(get_jwt_identity())
    return resp([i.model_dump(include={
        'id', 'nickname', 'signature', 'avatar_url', 'vip_deadline', 'block_deadline'}) for i in stars])


@bp.route('/follow-fans', methods=['post'])
@custom_jwt()
def follow_fans():
    """我的粉丝"""
    fans = dao.follow_fans(get_jwt_identity())
    return resp([i.model_dump(include={
        'id', 'nickname', 'signature', 'avatar_url', 'vip_deadline', 'block_deadline'}) for i in fans])


@bp.route('/sign-out', methods=['post'])
@custom_jwt()
def sign_out():
    """销号"""
    dao.sign_out(get_jwt_identity())
    return resp(RespMsg.success)


@bp.route('/sign-out-off', methods=['post'])
@custom_jwt()
def sign_out_off():
    """取消销号"""
    dao.sign_out_off(get_jwt_identity())
    return resp(RespMsg.success)


@bp.route('/set-black', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def set_black(black: UserId):
    """拉黑"""
    if not dao.exist(black.id):
        return resp(RespMsg.user_not_exist, -1)

    dao.set_black(g.user_id, black.id)
    return resp(RespMsg.success)


@bp.route('/unset-black', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def unset_black(black: UserId):
    """解除拉黑"""
    dao.unset_black(g.user_id, black.id)
    return resp(RespMsg.success)


@bp.route('/black-list', methods=['post'])
@custom_jwt()
def black_list():
    """我的拉黑"""
    return resp([u.model_dump(include={'id', 'nickname'}) for u in dao.black_list(get_jwt_identity())])
