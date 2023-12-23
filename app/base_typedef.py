from pydantic import AnyUrl
from typing import Tuple, Annotated
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from pydantic.functional_serializers import PlainSerializer


def url_wrap(url: AnyUrl, nxt: SerializerFunctionWrapHandler) -> str:
    """自定义AnyUrl类型序列化"""
    _ = nxt
    return str(url)


def location_wrap(location: Tuple[float, float], nxt: SerializerFunctionWrapHandler) -> str:
    _ = nxt
    return f'point ({location[0]} {location[1]})'


URL = Annotated[AnyUrl, PlainSerializer(url_wrap)]
LOCATION = Annotated[Tuple[float, float],  PlainSerializer(location_wrap, return_type=str)]


def point(location: Tuple[float, float]):
    """坐标类型序列化"""
    return f'SRID=4326;point ({location[0]} {location[1]})'


if __name__ == '__main__':
    from pydantic import BaseModel


    class A(BaseModel):
        location: LOCATION


    a = A(location=[1, 2])

    print(A(location=[1, 2]).model_dump())


