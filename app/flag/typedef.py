from datetime import datetime
from pydantic import constr
from typing import Optional, Tuple, List, Union
from app.typedef import UUID, LOCATION, REQ_LOCATION
from app.util import Model
from typedef import Order


_FLAG_CONTENT = constr(max_length=300)
_COMMENT_CONTENT = constr(max_length=100)


class Flag(Model):
    id: Optional[UUID]
    user_id: Optional[int]
    location: Optional[LOCATION]
    name: Optional[str]
    content: Optional[_FLAG_CONTENT]
    type: Optional[int]
    is_open: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    pictures: Optional[List[str]]


class Comment(Model):
    id: Optional[int]
    flag_id: Optional[int]
    user_id: Optional[int]
    content: Optional[_COMMENT_CONTENT]
    root_comment_id: Optional[int]
    location: Optional[LOCATION]
    prefix: Optional[str]
    comment_time: Optional[datetime]


class AddFlag(Flag):
    user_id: int
    location: REQ_LOCATION
    name: str
    content: _FLAG_CONTENT

    type: int
    is_open: int
    pictures: List[str]


class UpdateFlag(AddFlag):
    id: UUID


class GetFlagBy(Order):
    by: str
    key: Union[int, Tuple[float, float]]
    distance: Optional[Tuple[float, float]]


class FlagType(Model):
    type: int


class SetFlagType(FlagType):
    id: UUID


class GetFlagByWithType(GetFlagBy, FlagType):
    ...


class GetFlagCountByDistance(FlagType, Model):
    key: Tuple[float, float]
    distance: Optional[Tuple[float, float]]


class FlagId(Model):
    id: UUID


class AddComment(Model):
    flag_id: int
    content: _COMMENT_CONTENT
    location: REQ_LOCATION


class AddSubComment(AddComment):
    root_comment_id: int
    ask_user_id: int


class CommentSubResp(Model):
    id: int
    content: _COMMENT_CONTENT
    prefix: str
    comment_time: datetime


class CommentResp(Model):
    id: int
    content: _COMMENT_CONTENT
    prefix: str
    comment_time: datetime
    sub_comment: List[CommentSubResp]
