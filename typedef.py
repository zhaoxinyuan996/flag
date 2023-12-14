from pydantic.v1 import validator

from app.util import Model


class Order(Model):
    order: str
    asc: bool


class Page(Model):
    limit: int
    offset: int
