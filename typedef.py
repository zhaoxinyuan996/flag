from enum import Enum
from typing import Optional

from app.util import Model


class OrderField(Enum):
    """重写"""
    ...


class OrderSc(Enum):
    asc = 'asc'
    desc = 'desc'


class Order(Model):
    order: OrderField
    asc: OrderSc = OrderSc.asc

    @property
    def order_by(self):
        return f' {self.order.value} {self.asc.value}'


class Page(Model):
    """滚动翻页, t o d o 时间不在索引列上，但是可以根据id做范围标记"""
    compare: Optional[str]
    current: Optional[str]
