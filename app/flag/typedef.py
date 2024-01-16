from uuid import UUID
from datetime import datetime, timedelta

from flask import g
from pydantic import constr, confloat, conint
from typing import Optional, List
from app.base_typedef import LOCATION
from app.constants import UserClass
from app.user.controller import get_user_info
from app.util import Model
from typedef import Order, OrderField

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
    dead_line: Optional[datetime]

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
    parent_id: Optional[int]
    like_num: int
    distance: Optional[int]
    create_time: Optional[datetime]


class AddFlag(Model):
    name: constr(min_length=1, max_length=20)
    content: _FLAG_CONTENT

    location: LOCATION
    type: _TYPE
    status: _STATUS
    pictures: List[str]
    ico_name: constr(max_length=20)
    temp: bool

    @property
    def dead_line(self):
        if self.temp:
            user_class = get_user_info().user_class
            if user_class is UserClass.vip:
                return datetime.now() + timedelta(hours=24)
            elif user_class is UserClass.normal:
                return datetime.now() + timedelta(hours=1)
            else:
                return '-infinity'
        else:
            return None


class UpdateFlag(Model):
    id: UUID
    name: constr(min_length=1, max_length=20)
    content: _FLAG_CONTENT
    type: _TYPE
    status: _STATUS
    pictures: List[str]
    ico_name: constr(max_length=20)


class FlagPictures(Model):
    id: UUID
    pictures: List[str]


class GetFlagByOrderField(OrderField):
    id = 'id'
    flag = 'flag'
    create_time = 'create_time'


class GetFlagByOrder(Order):
    order: GetFlagByOrderField


class GetFlagByUser(GetFlagByOrder):
    id: Optional[UUID]


class GetFlagByFlag(Model):
    id: UUID


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


class OpenFlag(Flag):
    # 匿名或者删除
    user_id: Optional[UUID]
    nickname: Optional[str]
    avatar_name: Optional[str]
    # 相关
    is_like: bool = False
    is_fav: bool = False
    # 统计
    like_num: int = 0
    fav_num: int = 0
    comment_num: int = 0

    def __init__(self, **kwargs):
        # 匿名标记
        if kwargs['status'] & 0b10 == 0b10 and kwargs['user_id'] != g.user_id:
            kwargs['user_id'] = kwargs['nickname'] = kwargs['avatar_name'] = None
        super().__init__(**kwargs)


class FlagId(Model):
    id: UUID


class CommentId(Model):
    id: int


class AddComment(Model):
    flag_id: UUID
    content: _COMMENT_CONTENT
    location: LOCATION
    show_distance: bool
    distance: Optional[int]
    # 子评论属性
    parent_id: Optional[int]


class DeleteComment(Model):
    flag_id: UUID
    parent_id: Optional[int]


class CommentResp(Model):
    id: int
    owner: bool
    like_num: int
    user_id: UUID
    avatar_name: str
    nickname: str
    content: _COMMENT_CONTENT
    parent_id: Optional[int]
    distance: Optional[int]
    create_time: datetime


class FlagStatistics(Model):
    flag_id: Optional[UUID]
    like_users: Optional[dict]
    fav_users: Optional[dict]
    comment_users: Optional[dict]
    update_time: datetime
