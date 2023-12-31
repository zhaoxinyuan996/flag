from datetime import datetime
from uuid import UUID

from pydantic import constr, confloat, conint
from typing import Optional, List, Union
from app.base_typedef import LOCATION
from app.util import Model
from typedef import Order


_TYPE = conint(ge=0, le=1)
_STATUS = conint(ge=0, le=3)
_FLAG_CONTENT = constr(max_length=300)
_COMMENT_CONTENT = constr(max_length=100)


'''
status字段是int值，状态保存为位
1           1
anonymous   hide
'''


class Flag(Model):
    id: Optional[UUID]
    user_id: Optional[UUID]
    location: Optional[LOCATION]
    name: Optional[str]
    content: Optional[_FLAG_CONTENT]
    type: Optional[_TYPE]
    status: Optional[_STATUS]
    user_class: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    pictures: Optional[List[str]]
    ico_name: Optional[str]

    @property
    def hide(self) -> bool:
        return bool(self.status & 0b1)

    @property
    def anonymous(self) -> bool:
        return bool(self.status & 0b10)


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
    name: constr(min_length=1, max_length=20)
    content: _FLAG_CONTENT

    type: _TYPE
    status: _STATUS
    pictures: List[str]
    ico_name: constr(max_length=20)


class UpdateFlag(AddFlag):
    id: UUID


class GetFlagBy(Order):
    by: Optional[str]
    key: Union[None, UUID, LOCATION]


class FlagType(Model):
    type: _TYPE = 0


class SetFlagType(FlagType):
    id: UUID


class GetFlagByMap(FlagType):
    location: LOCATION
    distance: confloat(le=100000)


class FlagRegion(Model):
    region_name: str
    flag_num: int
    location: LOCATION


class FavFlag(Model):
    id: Optional[UUID]
    user_id: Optional[UUID]
    location: Optional[LOCATION]
    name: Optional[str]
    content: Optional[_FLAG_CONTENT]
    type: Optional[_TYPE]
    user_class: Optional[int]
    update_time: Optional[datetime]
    ico_name: Optional[str]


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
