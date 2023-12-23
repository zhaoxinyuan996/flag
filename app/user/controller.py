import logging
import os
import re
import random
import requests
from app.user.dao import dao
from datetime import datetime
from functools import partial
from flask import Blueprint, request, g
from app.util import resp, custom_jwt, args_parse
from app.constants import RespMsg, allow_picture_type, user_picture_size, UserLevel, FileType, AppError
from app.user.typedef import SignIn, SignUp, UserId, SignWechat, SetUserinfo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity
from common.job import DelayJob
from util.config import config
from util.database import db
from util.file_minio import file_minio

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')
wechat_config = config['wechat-miniapp']

username_pattern = re.compile(r'^[a-zA-Z0-9_-]{4,16}$')
password_pattern = re.compile(r'.*(?=.{6,16})(?=.*\d)(?=.*[A-Z])(?=.*[a-z]).*$')

log = logging.getLogger(__name__)


def get_user_level() -> UserLevel:
    """获取用户级别，后面用redis存"""
    user_id = get_jwt_identity()
    user = dao.get_level(user_id)
    if not user:
        raise AppError(RespMsg.user_not_exist)
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


def exists_black_list(user_id: int, black_id: int) -> bool:
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
        DelayJob.job_queue.put(partial(get_location, user_id, request.remote_addr))
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
    open_id = str(res.json()['openid'])
    user_id = dao.wechat_exist(open_id)
    new = False
    if user_id is None:
        new = True
        from app import app
        with app.app_context():
            user_id = dao.third_part_sigh_up_third('wechat', open_id, '')
            dao.third_part_sigh_up_user(user_id)
            db.session.commit()

    access_token = create_access_token(identity=user_id)
    print(access_token)
    return resp(RespMsg.user_sign_in_success, user_id=user_id, new=new, access_token=access_token)


@bp.route('/refresh-jwt', methods=['post'])
@custom_jwt()
def refresh_jwt():
    """更新jwt，要结合更多的redis？用户状态控制？"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    DelayJob.job_queue.put(partial(get_location, user_id, request.remote_addr))
    return resp(RespMsg.user_sign_in_success, access_token=access_token)


@bp.route('/user-info', methods=['post'])
@custom_jwt()
def user_info():
    # 查看别人的信息
    if request.data:
        user_id = str(request.json['id'])
        res = dao.user_info(user_id)
    # 查看自己的信息
    else:
        res = dao.user_info(get_jwt_identity())
    if not res:
        return resp(RespMsg.user_not_exist, -1)
    return resp(res.model_dump(include={
        'id', 'nickname', 'username', 'signature', 'avatar_url', 'vip_deadline',
        'block_deadline', 'belong', 'location'
    }))


@bp.route('/upload-avatar', methods=['post'])
@custom_jwt()
def upload_avatar():
    """设置头像"""
    user_id = get_jwt_identity()
    level = get_user_level()
    suffix = request.files['pic'].filename.rsplit('.', 1)[1]
    if suffix not in allow_picture_type:
        return resp(RespMsg.user_picture_format_error + str(allow_picture_type), -1)
    b = request.files['pic'].stream.read()
    if len(b) > user_picture_size:
        return resp(RespMsg.too_large, -1)
    file_minio.upload(f'{user_id}.{suffix}', FileType.head_pic, b, level == UserLevel.vip)
    url = file_minio.get_file_url(FileType.head_pic, f'{user_id}.{suffix}')
    dao.set_userinfo(user_id, {'avatar_url': url})
    return resp(RespMsg.success)


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
    dao.set_userinfo(get_jwt_identity(), info)
    return resp(RespMsg.success)


@bp.route('/follow-add', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_add(user: UserId):
    """关注"""
    dao.follow_add(get_jwt_identity(), user.id)
    return resp(RespMsg.success)


@bp.route('/follow-remove', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def follow_remove(user: UserId):
    """取关"""
    dao.follow_remove(get_jwt_identity(), user.id)
    return resp(RespMsg.success)


@bp.route('/follow-star', methods=['post'])
@custom_jwt()
def follow_star():
    """我的关注"""
    stars = dao.follow_star(get_jwt_identity())
    return resp([i.model_dump(include={
        'id', 'nickname', 'signature', 'vip_deadline', 'block_deadline'}) for i in stars])


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

    dao.set_black(get_jwt_identity(), black.id)
    return resp(RespMsg.success)


@bp.route('/unset-black', methods=['post'])
@args_parse(UserId)
@custom_jwt()
def unset_black(black: UserId):
    """解除拉黑"""
    dao.unset_black(get_jwt_identity(), black.id)
    return resp(RespMsg.success)


@bp.route('/black-list', methods=['post'])
@custom_jwt()
def black_list():
    """我的拉黑"""
    return resp([u.model_dump(include={'id', 'nickname'}) for u in dao.black_list(get_jwt_identity())])
