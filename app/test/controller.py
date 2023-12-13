import os
from flask import Blueprint
from app.test.dao import dao

module_name = os.path.basename(os.path.dirname(__file__))
bp = Blueprint(module_name, __name__, url_prefix=f'/{module_name}')


@bp.route('/', methods=['get', 'post'])
def bp_test():
    res = dao.test()
    print(res[0].dict())
    raise
    return str(res)
