import random
import string
from typing import Tuple, Optional, List
from uuid import UUID

from app.base_dao import Dao
from app.user.typedef import User, OtherUser, OverviewUser, SelfUser

# vip_deadline = 'infinity'
vip_deadline = 'current_timestamp'
default_avatar_filename = 'default.png'

overview_fields = 'u.id, u.nickname, u.signature, u.avatar_name, u.is_man, u.vip_deadline, u.block_deadline, u.flag_num'


def ran_nickname():
    """8位随机字符当昵称"""
    return 'user-' + ''.join(random.sample(string.ascii_letters + string.digits, 8))


class UserDao(Dao):
    def sign_up(self, username: str, password: str, nickname: str) -> int:
        sql = ('insert into users (username, password, nickname, signature, create_time, vip_deadline, block_deadline, '
               "alive_deadline) values(:username, :password, :nickname, '说点想说的吧！', current_timestamp, "
               f"{vip_deadline}, '-infinity', current_timestamp) "
               "returning id")
        return self.execute(sql, username=username, password=password, nickname=nickname or ran_nickname())

    def sign_in(self, username: str) -> Optional[Tuple[UUID, str]]:
        sql = 'select id, password from users where username=:username'
        return self.execute(sql, username=username)

    def self_user_info(self, user_id: UUID) -> Optional[SelfUser]:
        sql = ('select id, username, nickname, phone, is_man, avatar_name, bg_avatar_name, signature, '
               'flag_num, create_time, alive_deadline, vip_deadline, block_deadline, belong, local, belong, hidden '
               'from users where id=:user_id')
        return self.execute(sql, user_id=user_id)

    def other_user_info(self, other_id: UUID, user_id: UUID) -> Optional[OtherUser]:
        sql = ('select id, nickname, is_man, signature, avatar_name, flag_num, is_man, '
               'vip_deadline, block_deadline, '
               'f.fans_id is not null is_follow, '
               'b.black_id is not null is_black '
               'from users u left join follow f on u.id=f.star_id '
               'left join black_list b on u.id=b.black_id and b.user_id=:user_id '
               'and f.fans_id=:user_id  where u.id=:other_id')
        return self.execute(sql, other_id=other_id, user_id=user_id)

    def follow_add(self, fans_id: UUID, star_id: UUID):
        sql = 'insert into follow (fans_id ,star_id) values(:fans_id, :star_id)'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_remove(self, fans_id: UUID, star_id: UUID):
        sql = 'delete from follow where fans_id=:fans_id and star_id=:star_id'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_star(self, user_id: UUID) -> List[OverviewUser]:
        sql = (f'select {overview_fields} '
               'from follow f inner join users u '
               'on f.star_id=u.id where f.fans_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def follow_fans(self, user_id: UUID) -> List[OverviewUser]:
        sql = (f'select {overview_fields} '
               'from follow f inner join users u '
               'on f.fans_id=u.id where f.star_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def sign_out(self, user_id: UUID):
        sql = "insert into sign_out_users (user_id, out_time) values(:user_id, current_date::timestamp + '3days')"
        return self.execute(sql, user_id=user_id)

    def sign_out_off(self, user_id: UUID):
        sql = "delete from sign_out_users where user_id=:user_id"
        return self.execute(sql, user_id=user_id)

    def get_user_info(self, user_id: UUID) -> Optional[User]:
        sql = 'select * from users where id=:user_id'
        return self.execute(sql, user_id=user_id)

    def set_black(self, user_id: UUID, black_id: UUID):
        sql = ('insert into black_list (user_id, black_id, update_time) '
               'values(:user_id, :black_id, current_timestamp) '
               'on conflict(user_id, black_id) do update set update_time=current_timestamp')
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def unset_black(self, user_id: UUID, black_id: UUID):
        sql = 'delete from black_list where user_id=:user_id and black_id=:black_id'
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def black_list(self, user_id: UUID) -> List[OverviewUser]:
        sql = (f'select {overview_fields} '
               'from black_list b inner join users u '
               'on b.black_id=u.id where b.user_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def exist(self, user_id: UUID) -> Optional[int]:
        sql = 'select 1 from users where id=:user_id'
        return self.execute(sql, user_id=user_id)

    def exist_black_list(self, user_id: UUID, black_id: UUID) -> Optional[int]:
        sql = ('select exists (select 1 from black_list where user_id=:user_id and black_id=:black_id) '
               'or not exists(select 1 from users where id=:user_id)')
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def wechat_exist(self, open_id: str) -> Optional[UUID]:
        sql = "select id from third_users where login_type='wechat' and open_id=:open_id"
        return self.execute(sql, open_id=open_id)

    def third_part_sigh_up_third(self, login_type: str, open_id: str, access_token: str) -> UUID:
        sql = ('insert into third_users (id, login_type, open_id, access_token) values '
               f"(gen_random_uuid(), :login_type, :open_id, :access_token) returning id")
        return self.execute(sql, login_type=login_type, open_id=open_id, access_token=access_token)

    def third_part_sigh_up_user(self, user_id: UUID) -> int:
        sql = ('insert into users (id, nickname, signature, avatar_name, create_time, vip_deadline, '
               'block_deadline, alive_deadline, hidden) values'
               f"(:user_id, :nickname, '说点想说的吧！', :avatar_name, "
               f"current_timestamp, {vip_deadline}, '-infinity', current_timestamp, false) returning id")
        return self.execute(sql, user_id=user_id, nickname=ran_nickname(), avatar_name=default_avatar_filename)

    def get_avatar_filename(self, user_id: UUID) -> str:
        sql = 'select avatar_name from users where id=:user_id'
        return self.execute(sql, user_id=user_id)

    def set_avatar_filename(self, user_id: UUID, avatar_name: str) -> User:
        sql = 'update users set avatar_name=:avatar_name where id=:user_id returning *'
        return self.execute(sql, user_id=user_id, avatar_name=avatar_name)

    def set_userinfo(self, user_id: UUID, info: dict) -> User:
        settings = ','.join(f"{k}=:{k}" for k, v in info.items() if v is not None)
        sql = (f'update users set {settings} '
               'where id=:user_id returning *')
        return self.execute(sql, user_id=user_id, **info)

    def add_flag(self, user_id: UUID) -> User:
        sql = 'update users set flag_num=flag_num+1 where id=:user_id returning *'
        return self.execute(sql, user_id=user_id)

    def delete_flag(self, user_id: UUID) -> User:
        sql = 'update users set flag_num=flag_num-1 where id=:user_id returning *'
        return self.execute(sql, user_id=user_id)


dao: UserDao = UserDao()
