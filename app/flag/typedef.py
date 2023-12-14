from datetime import datetime
from typing import Optional, Tuple, List, Union
from app.util import Model
from typedef import Order


class Flag(Model):
    id: Optional[int]
    user_id: Optional[int]
    location_x: Optional[float]
    location_y: Optional[float]
    content: Optional[str]
    type: Optional[int]
    is_open: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    pictures: Optional[List[str]]


class Comment(Model):
    id: Optional[int]
    flag_id: Optional[int]
    user_id: Optional[int]
    content: Optional[str]
    root_comment_id: Optional[int]
    location_x: Optional[float]
    location_y: Optional[float]
    prefix: Optional[str]
    comment_time: Optional[datetime]


class AddFlag(Flag):
    user_id: int
    location: Tuple[float, float]
    content: str

    is_open: int
    pictures: List[str]


class GetFlagBy(Order):
    by: str
    key: Union[int, Tuple[float, float]]
    distance: Optional[Tuple[float, float]]


class GetFlagCountByDistance(Model):
    key: Tuple[float, float]
    distance: Optional[Tuple[float, float]]
