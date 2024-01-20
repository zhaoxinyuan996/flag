import os
from flask import Blueprint, g
from app.user.dao import dao as user_dao
from app.util import custom_jwt, resp

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/api/{module_name}')


# 没有任何io的测试接口
@bp.route('/call-cpu', methods=['get'])
@custom_jwt()
def call_cpu():
    user_id = g.user_id
    return resp(user_id)


# 简单查表的测试接口
@bp.route('/user-info', methods=['get'])
@custom_jwt()
def user_info():
    user_id = g.user_id
    res = user_dao.self_user_info(user_id)
    print(res)
    return resp(res.model_dump())
