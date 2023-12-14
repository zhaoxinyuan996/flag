from typing import Optional

from app.util import Model


class Order(Model):
    order: str = 'id'
    asc: str = 'asc'


class Page(Model):
    """滚动翻页, t o d o 时间不在索引列上，但是可以根据id做范围标记"""
    compare: Optional[str]
    current: Optional[str]
