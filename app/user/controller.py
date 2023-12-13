import os
import re
from sqlalchemy import exc
from app.user.dao import dao
from datetime import datetime
from flask import Blueprint, request, send_file
from app.util import resp, custom_jwt, args_parse
from app.constants import message, allow_picture_type, user_picture_size, UserLevel, user_picture_folder
from app.user.typedef import SignUpIn, SetUserNickname, SetUserSignature, UserId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')


pattern = re.compile(r'.*(?=.{6,})(?=.*\d)(?=.*[A-Z])(?=.*[a-z]).*$')


@bp.route('/sign-up', methods=['post'])
@args_parse(SignUpIn)
def sign_up(user: SignUpIn):
    # 密码强度，//密码强度正则，最少6位，包括至少1个大写字母，1个小写字母，1个数字
    if not pattern.match(user.password):
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
        return resp(message.user_sign_in_success, user_id=user_id, access_token=access_token)
    else:
        return resp(message.user_sign_in_password_error, -1)


@bp.route('/user-info', methods=['post'])
@custom_jwt()
def user_info():
    res = dao.user_info(get_jwt_identity())
    return resp(res.model_dump(include={'id', 'nickname', 'username', 'signature', 'vip_deadline'}))


@bp.route('/set-profile-picture', methods=['post'])
@custom_jwt()
def set_profile_picture():
    """设置头像"""
    user_id = get_jwt_identity()
    suffix = request.files['pic'].filename.rsplit('.', 1)[1]
    if suffix not in allow_picture_type:
        return resp(message.user_picture_format_error + str(allow_picture_type), -1)
    b = request.files['pic'].stream.read()
    if len(b) > user_picture_size:
        return resp(message.too_large, -1)
    with open(os.path.join(user_picture_folder, f'{user_id}-profile-picture'), 'wb') as f:
        f.write(b)
    return resp(message.success)


@bp.route('/get-profile-picture', methods=['post'])
@custom_jwt()
def get_profile_picture():
    """获取头像"""
    path = os.path.join(user_picture_folder, f'{get_jwt_identity()}-profile-picture')
    if os.path.exists(path):
        return send_file(path)
    return ''


@bp.route('/set-nickname', methods=['post'])
@args_parse(SetUserNickname)
@custom_jwt()
def set_nickname(user_nickname: SetUserNickname):
    """设置昵称"""
    if len(user_nickname.nickname) > 20:
        return resp(message.too_long, -1)
    dao.set_user_nickname(get_jwt_identity(), user_nickname.nickname)
    return resp(message.success)


@bp.route('/set-signature', methods=['post'])
@args_parse(SetUserSignature)
@custom_jwt()
def set_signature(user_signature: SetUserSignature):
    """设置签名"""
    if len(user_signature.signature) > 200:
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


def get_user_level() -> int:
    if dao.get_level(get_jwt_identity()) > datetime.now():
        return UserLevel.vip
    return UserLevel.normal
