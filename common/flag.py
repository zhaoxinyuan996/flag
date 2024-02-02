r"""
标记延时操作
"""
import logging
from threading import Lock
from uuid import UUID

from util import db
from app.base_dao import base_dao
from app.util import StatisticsUtil
from common.app_shadow import placeholder_app
from util.msg_middleware import mq_flag_like
from util.wrappers import thread_lock


log = logging.getLogger(__name__)


statistics_util = StatisticsUtil()


class FlagLike:
    """
    定期刷新flag_statistics表，此表所有写操作都在这里完成
    num字段可以采用非严格模式，定时跑批更新精确num字段
    """
    lock = Lock()
    # 元组0是删除的，元组1是新增的

    @thread_lock(lock)
    def add(self, user_id: UUID, flag_id: UUID, key: str, num: int):
        return statistics_util.add(user_id, flag_id, key, num)

    @thread_lock(lock)
    def flush(self):
        if all_sql := statistics_util.build_flag_statistics_sql():
            with placeholder_app.app_context():
                base_dao.execute(';'.join(all_sql))
                db.session.commit()


flag_like = FlagLike()
mq_flag_like.register_cb(flag_like.add)
