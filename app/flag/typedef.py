from datetime import datetime
from uuid import UUID

from pydantic import constr, confloat
from typing import Optional, List, Union
from app.base_typedef import LOCATION
from app.util import Model
from typedef import Order


_FLAG_CONTENT = Optional[constr(max_length=300)]
_COMMENT_CONTENT = constr(max_length=100)


class Flag(Model):
    id: Optional[UUID]
    user_id: Optional[UUID]
    location: Optional[LOCATION]
    name: Optional[str]
    content: Optional[_FLAG_CONTENT]
    type: Optional[int]
    is_open: Optional[int]
    user_class: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    pictures: Optional[List[str]]
    ico_name: Optional[str]


class Comment(Model):
    id: Optional[int]
    flag_id: Optional[UUID]
    user_id: Optional[UUID]
    content: Optional[_COMMENT_CONTENT]
    root_comment_id: Optional[int]
    location: Optional[LOCATION]
    prefix: Optional[str]
    comment_time: Optional[datetime]


class AddFlag(Flag):
    user_id: UUID
    location: LOCATION
    name: constr(min_length=1, max_length=20)
    content: _FLAG_CONTENT

    type: int
    is_open: int
    pictures: List[str]
    ico_name: constr(max_length=20)


class UpdateFlag(AddFlag):
    id: UUID


class GetFlagBy(Order):
    by: Optional[str]
    key: Union[None, UUID, LOCATION]


class FlagType(Model):
    type: int = 0


class SetFlagType(FlagType):
    id: UUID


class GetFlagByMap(FlagType):
    type: Optional[int]
    location: LOCATION
    distance: confloat(le=100000)


class GetFlagByMapCount(FlagType):
    type: Optional[int] = 0
    location: LOCATION
    distance: confloat(le=100000)


class FlagId(Model):
    id: UUID


class AddComment(Model):
    flag_id: UUID
    content: _COMMENT_CONTENT
    location: LOCATION
    show_distance: bool


class AddSubComment(AddComment):
    root_comment_id: int
    ask_user_id: UUID


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
