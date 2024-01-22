from enum import Enum
from app.util import Model
from pydantic import AnyUrl, confloat
from typing import Tuple, Annotated, Optional
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from pydantic.functional_serializers import PlainSerializer


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


def url_wrap(url: AnyUrl, nxt: SerializerFunctionWrapHandler) -> str:
    """自定义AnyUrl类型序列化"""
    _ = nxt
    return str(url)


URL = Annotated[AnyUrl, PlainSerializer(url_wrap)]
LOCATION = Tuple[confloat(ge=-90, le=90), confloat(ge=-180, le=180)]


def point(location: Tuple[float, float]):
    """坐标类型序列化，pg中顺序是精度纬度"""
    return f'SRID=4326;point ({location[1]} {location[0]})'


if __name__ == '__main__':
    from pydantic import BaseModel


    class A(BaseModel):
        location: LOCATION


    a = A(location=[1, 2])

    print(A(location=[1, 2]).model_dump())
