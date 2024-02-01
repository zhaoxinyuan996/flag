r"""
用户延时操作
"""
import logging
import random
from uuid import UUID
import requests
from app.base_dao import base_dao
from common.app_shadow import placeholder_app
from util import db

log = logging.getLogger(__name__)


def refresh_user_mq(user_id: UUID, ip: str):
    """获取ip位置"""
    def _get_local():
        try:
            data = requests.get(api % ip).json()
            log.info(str(data))
            for key in keys:
                data = data[key]
            return data
        except requests.RequestException:
            return None
        except Exception as e:
            log.exception(e)
            return None

    # if ip == '127.0.0.1':
    #     return

    apis = (
        ('https://www.ip.cn/api/index?type=1&ip=%s', ('address',)),
        # 百度这个嵌套了一个数组，先不用这个
        # ('http://opendata.baidu.com/api.php?query=%s&co=&resource_id=6006&oe=utf8', ('addr',)),
        ('https://searchplugin.csdn.net/api/v1/ip/get?ip=%s', ('data', 'address')),
        ('https://whois.pconline.com.cn/ipJson.jsp?ip=%s&json=true', ('addr',)),
        ('http://ip-api.com/json/%s?lang=zh-CN', ('regionName',)),
        ('http://whois.pconline.com.cn/ipJson.jsp?json=true&ip=%s', ('addr',)),
    )
    idx_list = [i for i in range(len(apis))]
    random.shuffle(idx_list)
    local = ''
    for i in idx_list:
        api, keys = apis[i]
        local = _get_local()
        if local:
            break
    with placeholder_app.app_context():
        base_dao.refresh(user_id, local=local)
        db.session.commit()
