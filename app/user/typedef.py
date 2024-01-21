from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import constr, conint
from app.constants import UserClass, FlagNum, UndefinedError
from app.util import Model


_NICKNAME = constr(max_length=20)
_SIGNATURE = constr(max_length=50)


class UserMixin:
    """抽象Mixin类"""
    @property
    def user_class(self) -> int:
        if self.block_deadline and self.block_deadline > datetime.now():
            return UserClass.block
        elif self.hidden is True:
            return UserClass.hidden
        elif self.vip_deadline and self.vip_deadline > datetime.now():
            return UserClass.vip
        else:
            return UserClass.normal

    @property
    def allow_flag_num(self) -> int:
        if self.user_class == UserClass.block:
            return 0
        elif self.user_class == UserClass.normal:
            return FlagNum.normal_user - self.flag_num
        elif self.user_class == UserClass.vip:
            return FlagNum.vip_user - self.flag_num
        elif self.user_class == UserClass.hidden:
            return FlagNum.hidden_user - self.flag_num
        raise UndefinedError('user class')


class User(Model, UserMixin):
    id: UUID

    nickname: _NICKNAME
    username: Optional[str]
    password: Optional[str]
    phone: Optional[int]
    is_man: Optional[bool]
    signature: Optional[_SIGNATURE]
    avatar_name: str
    bg_avatar_name: Optional[str]
    flag_num: int
    create_time: datetime
    vip_deadline: datetime
    block_deadline: datetime
    alive_deadline: datetime

    belong: Optional[str]
    local: Optional[str]
    hidden: bool


class SelfUser(Model, UserMixin):
    id: UUID

    nickname: _NICKNAME
    username: Optional[str]
    phone: Optional[int]
    is_man: Optional[bool]
    signature: Optional[_SIGNATURE]
    avatar_name: str
    bg_avatar_name: Optional[str]
    flag_num: int
    vip_deadline: datetime
    block_deadline: datetime


class QueryUser(Model):
    id: Optional[UUID] = None


class OverviewUser(Model):
    id: UUID
    nickname: _NICKNAME
    is_man: Optional[bool]
    flag_num: int

    signature: _SIGNATURE
    avatar_name: str

    vip_deadline: datetime
    block_deadline: datetime


class OtherUser(Model):
    id: UUID
    nickname: _NICKNAME
    is_man: Optional[bool]
    flag_num: int

    signature: _SIGNATURE
    avatar_name: str

    vip_deadline: datetime
    block_deadline: datetime

    is_follow: int
    is_black: int


class SignUp(Model):
    username: str
    password: str


class SignWechat(Model):
    code: str


class SignIn(Model):
    username: str
    password: str


class UserId(Model):
    id: UUID


class SetUserinfo(Model):
    nickname: Optional[_NICKNAME] = None
    is_man: Optional[bool] = None
    phone: Optional[conint(lt=19999999999)] = None
    signature: Optional[_SIGNATURE] = None


if __name__ == '__main__':
    ...
