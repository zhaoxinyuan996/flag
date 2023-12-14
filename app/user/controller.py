import logging
import os
import re
import random
import requests
from sqlalchemy import exc
from app.user.dao import dao
from datetime import datetime
from functools import partial
from flask import Blueprint, request, g
from app.util import resp, custom_jwt, args_parse
from app.constants import message, allow_picture_type, user_picture_size, UserLevel, FileType
from app.user.typedef import SignUpIn, SetUserNickname, SetUserSignature, UserId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity
from common.job import DelayJob
from util.database import db
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')


username_pattern = re.compile(r'^[a-zA-Z0-9_-]{4,16}$')
password_pattern = re.compile(r'.*(?=.{6,16})(?=.*\d)(?=.*[A-Z])(?=.*[a-z]).*$')

log = logging.getLogger(__name__)


@bp.route('/sign-up', methods=['post'])
@args_parse(SignUpIn)
def sign_up(user: SignUpIn):
    # 密码强度，密码强度正则，最少6位，包括至少1个大写字母，1个小写字母，1个数字
    if len(user.username) > 16 or not username_pattern.match(user.username):
        return resp(message.user_sign_up_username_weak, -1)
    if len(user.password) > 16 or not password_pattern.match(user.password):
        return resp(message.user_sign_up_password_weak, -1)

    user.password = generate_password_hash(user.password, method='pbkdf2:sha256')
    try:
        user_id = dao.sign_up(user.username, user.password)
    except exc.IntegrityError:
        return resp(message.user_sign_up_already_exist, -1)
    else:
        return resp(message.user_sign_up_success, user_id=user_id)


@bp.route('/sign-in', methods=['post'])
@args_parse(SignUpIn)
def sign_in(user: SignUpIn):
    res = dao.sign_in(user.username)
    if not res:
        return resp(message.user_sign_in_not_exist, -1)
    user_id, password = res
    if check_password_hash(password, user.password):
        access_token = create_access_token(identity=user_id)
        DelayJob.job_queue.put(partial(get_location, user_id, request.remote_addr))
        return resp(message.user_sign_in_success, user_id=user_id, access_token=access_token)
    else:
        return resp(message.user_sign_in_password_error, -1)


@bp.route('/refresh-jwt', methods=['post'])
@custom_jwt()
def refresh_kwt():
    """更新jwt，要结合更多的redis？用户状态控制？"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    DelayJob.job_queue.put(partial(get_location, user_id, request.remote_addr))
    return resp(message.user_sign_in_success, access_token=access_token)


@bp.route('/user-info', methods=['post'])
@custom_jwt()
def user_info():
    # 查看别人的信息
    if request.data:
        user_id = int(request.json['id'])
        res = dao.user_info(user_id)
    # 查看自己的信息
    else:
        res = dao.user_info(get_jwt_identity())
    if not res:
        return resp(message.user_sign_in_not_exist, -1)
    return resp(res.model_dump(include={
        'id', 'nickname', 'username', 'signature', 'profile_picture', 'vip_deadline',
        'block_deadline', 'belong', 'location'
    }))


@bp.route('/set-profile-picture', methods=['post'])
@custom_jwt()
def set_profile_picture():
    """设置头像"""
    user_id = get_jwt_identity()
    level = get_user_level()
    suffix = request.files['pic'].filename.rsplit('.', 1)[1]
    if suffix not in allow_picture_type:
        return resp(message.user_picture_format_error + str(allow_picture_type), -1)
    b = request.files['pic'].stream.read()
    if len(b) > user_picture_size:
        return resp(message.too_large, -1)
    file_minio.upload(f'{user_id}.{suffix}', FileType.head_pic, b, level == UserLevel.vip)
    url = file_minio.get_file_url(FileType.head_pic, f'{user_id}.{suffix}')
    dao.set_profile_picture(user_id, url)
    return resp(message.success)


@bp.route('/get-profile-picture', methods=['post'])
@custom_jwt()
def get_profile_picture():
    """获取头像"""
    url = file_minio.get_file_url(FileType.head_pic, str(get_jwt_identity()), thumbnail=False)
    return resp(message.success, url=url)


@bp.route('/set-nickname', methods=['post'])
@args_parse(SetUserNickname)
@custom_jwt()
def set_nickname(user_nickname: SetUserNickname):
    """设置昵称"""
    if len(user_nickname.nickname) > 16:
        return resp(message.too_long, -1)
    dao.set_user_nickname(get_jwt_identity(), user_nickname.nickname)
    return resp(message.success)


@bp.route('/set-signature', methods=['post'])
@args_parse(SetUserSignature)
@custom_jwt()
def set_signature(user_signature: SetUserSignature):
    """设置签名"""
    if len(user_signature.signature) > 50:
        return resp(message.too_long, -1)
    dao.set_user_signature(get_jwt_identity(), user_signature.signature)
    return resp(message.success)


@bp.route('/follow-add', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_add(user: UserId):
    """关注"""
    try:
        dao.follow_add(get_jwt_identity(), user.id)
    except exc.IntegrityError:
        return resp(message.success)
    return resp(message.success)


@bp.route('/follow-remove', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_remove(user: UserId):
    """取关"""
    dao.follow_remove(get_jwt_identity(), user.id)
    return resp(message.success)


@bp.route('/follow-star', methods=['post'])
@custom_jwt()
def follow_star():
    """我的关注"""
    stars = dao.follow_star(get_jwt_identity())
    return resp([i.model_dump(include={'nickname', 'username', 'signature'}) for i in stars])


@bp.route('/follow-fans', methods=['post'])
@custom_jwt()
def follow_fans():
    """我的粉丝"""
    fans = dao.follow_fans(get_jwt_identity())
    return resp([i.model_dump(include={'nickname', 'username', 'signature'}) for i in fans])


@bp.route('/sign-out', methods=['post'])
@custom_jwt()
def sign_out():
    """销号"""
    dao.sign_out(get_jwt_identity())
    return resp(message.success)


@bp.route('/sign-out-off', methods=['post'])
@custom_jwt()
def sign_out_off():
    """取消销号"""
    dao.sign_out_off(get_jwt_identity())
    return resp(message.success)


def get_user_level() -> UserLevel:
    """获取用户级别，后面用redis存"""
    user_id = get_jwt_identity()
    user = dao.get_level(user_id)
    if user.block_deadline > datetime.now():
        level = UserLevel.block
    elif user.vip_deadline > datetime.now():
        level = UserLevel.vip
    else:
        level = UserLevel.normal
    g.user_level = level
    return level


def get_location(user_id: int, ip: str):
    """获取ip位置"""
    from app import app

    def _get_location():
        try:
            data = requests.get(api + ip).json()
            log.info(str(data))
            return data[key]
        except requests.RequestException:
            return None
    apis = (
        ('http://ip.360.cn/IPQuery/ipquery?ip=', 'data'),
        ('http://www.ip508.com/ip?q=', 'addr'),
        ('http://whois.pconline.com.cn/ipJson.jsp?json=true&ip=', 'addr'),
    )
    idx_list = [i for i in range(len(apis))]
    random.shuffle(idx_list)
    location = ''
    for i in idx_list:
        api, key = apis[i]
        location = _get_location()
        if location:
            break
    with app.app_context():
        dao.refresh(user_id, location=location)
        db.session.commit()
