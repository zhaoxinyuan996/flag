import os
import shutil
import logging
from app import message
from app.flag.dao import dao
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.constants import UserLevel, flag_picture_size
from app.user.controller import get_user_level
from app.user.dao import dao as user_dao
from app.flag.typedef import Flag, AddFlag
from app.util import args_parse, resp, custom_jwt, get_request_list
from util.database import db

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')

log = logging.getLogger(__name__)


@bp.route('/add', methods=['post'])
@custom_jwt()
def add():
    pictures = request.files.getlist('pic')
    level = get_user_level()
    if level == UserLevel.normal and len(pictures) > 1:
        return resp(message.too_large)
    elif level == UserLevel.vip and len(pictures) > 9:
        return resp(message.too_large)
    length = 0
    datas = []
    for p in pictures:
        data = p.stream.read()
        length += len(data)
        if length > flag_picture_size:
            return resp(message.too_large)
        datas.append(data)

    flag = AddFlag(**get_request_list(request.form))
    flag.user_id = get_jwt_identity()
    pic_folder = None
    if pictures:
        flag.has_picture = 1
    try:
        with db.auto_commit():
            flag.id = dao.add(flag)
            assert flag.id

            # pic_folder = os.path.join(flag_picture_folder, str(flag.id))
            if not os.path.exists(pic_folder):
                os.mkdir(pic_folder)

            for i, data in enumerate(datas):
                with open(os.path.join(pic_folder, str(i)), 'wb') as f:
                    f.write(data)
    except Exception as e:
        log.exception(e)
        if pic_folder:
            shutil.rmtree(pic_folder)

    return resp(message.success)
