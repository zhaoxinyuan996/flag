r"""
标记延时操作
"""
import logging
from threading import Lock
from typing import Dict, Tuple, Set
from uuid import UUID
from util import db
from app.base_dao import base_dao
from common.app_shadow import placeholder_app
from util.msg_middleware import mq_flag_statistics
from util.wrappers import thread_lock


log = logging.getLogger(__name__)


class Statistics:
    """
    定期刷新flag_statistics表，此表所有写操作都在这里完成
    num字段可以采用非严格模式，定时跑批更新精确num字段
    """
    lock = Lock()
    # 元组0是删除的，元组1是新增的

    def __init__(self):
        self.statistics_cache: Dict[UUID, Dict[str, Tuple[Set[UUID], Set[UUID]]]] = {}

    @thread_lock(lock)
    def add(self, user_id: UUID, flag_id: UUID, key: str, num: int):
        # num是0则删除，num是1则新增
        # 嵌套了好几层，就不用default dict了
        if flag_id not in self.statistics_cache:
            self.statistics_cache[flag_id] = {}
        if key not in self.statistics_cache[flag_id]:
            self.statistics_cache[flag_id][key] = (set(), set())
        self.statistics_cache[flag_id][key][num].add(user_id)

    @thread_lock(lock)
    def flush(self):
        all_sql = []
        for flag_id, kv in self.statistics_cache.items():
            loop = []
            for key, tuples in kv.items():
                # 剔除共有的user_id
                del_users, add_users = tuples
                reject: Set[UUID] = del_users & add_users
                del_users ^= reject
                add_users ^= reject
                if del_users:
                    loop.extend((f"{key}_users = delete({key}_users, '{uuid}')" for uuid in del_users))
                if add_users:
                    loop.extend((f"{key}_users ['{uuid}']=current_timestamp::text" for uuid in add_users))
                num_diff = len(add_users) - len(del_users)
                if num_diff:
                    loop.append(f"{key}_num={key}_num+{num_diff} ")
            if loop:
                all_sql.append(f"update flag_statistics set {','.join(loop)}")
        if all_sql:
            self.statistics_cache = {}
            with placeholder_app.app_context():
                base_dao.execute(';'.join(all_sql))
                db.session.commit()


statistics = Statistics()
mq_flag_statistics.register_cb(statistics.add)
