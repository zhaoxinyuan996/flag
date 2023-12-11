import os
from flask import Blueprint
from app.user.dao import dao
from app.util import parse, resp
from app.constants import message
from app.user.typedef import SignUp0d1
from werkzeug.security import generate_password_hash


module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')


@bp.route('/v0.1/sign-up', methods=['post'])
def sign_up():
    user: SignUp0d1 = parse(SignUp0d1)
    user.password = generate_password_hash(user.password)
    user_id = dao.sign_up_0_1(user.username, user.password)
    return resp(message.user_sign_up_success, user_id=user_id)
