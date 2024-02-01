r"""
标记延时操作
"""
from collections import defaultdict
from typing import Dict
from uuid import UUID

from app.flag.dao import dao


class Statistics:
    # 缓存
    statistics_cache: Dict[UUID, Dict[UUID, int]] = defaultdict(dict)

    def add(self, user_id: UUID, flag_id: UUID, key: str):
        self.statistics_cache[user_id][flag_id][key]

dao.set_statistics()