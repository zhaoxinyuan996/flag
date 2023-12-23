import random
import string
from typing import Tuple, Optional, List
from app.base_dao import Dao
from app.base_typedef import LOCATION
from app.user.typedef import User

vip_deadline = 'infinity'


def ran_nickname():
    """8位随机字符当昵称"""
    return 'user-' + ''.join(random.sample(string.ascii_letters + string.digits, 8))


class UserDao(Dao):
    def sign_up(self, username: str, password: str, nickname: str) -> int:
        sql = ('insert into users (username, password, nickname, signature, create_time, vip_deadline, block_deadline, '
               "alive_deadline) values(:username, :password, :nickname, '说点想说的吧！', current_timestamp, "
               f"{vip_deadline}', '-infinity', current_timestamp) "
               "returning id")
        return self.execute(sql, username=username, password=password, nickname=nickname or ran_nickname())

    def sign_in(self, username: str) -> Optional[Tuple[int, str]]:
        sql = 'select id, password from users where username=:username'
        return self.execute(sql, username=username)

    def user_info(self, user_id: str) -> Optional[User]:
        sql = ('select id, username, nickname, avatar_url, signature, '
               'vip_deadline, block_deadline, belong, location '
               'from users where id=:user_id')
        return self.execute(sql, user_id=user_id)

    def refresh(self, user_id: str, location: LOCATION):
        sql = ('update users set alive_deadline=current_timestamp, location=point(:location) '
               'where id=:user_id')
        return self.execute(sql, user_id=user_id, location=location)

    def follow_add(self, fans_id: int, star_id: int):
        sql = 'insert into follow (fans_id ,star_id) values(:fans_id, :star_id)'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_remove(self, fans_id: int, star_id: int):
        sql = 'delete from follow where fans_id=:fans_id and star_id=:star_id'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_star(self, user_id: str) -> List[User]:
        sql = ('select u.id, u.nickname, u.vip_deadline, u.block_deadline, u.signature '
               'from follow f inner join users u '
               'on f.star_id=u.id where f.fans_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def follow_fans(self, user_id: str) -> List[User]:
        sql = ('select u.id, u.nickname, u.username, u.signature from follow f inner join users u '
               'on f.fans_id=u.id where f.star_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def sign_out(self, user_id: str):
        sql = "insert into sign_out_users (user_id, out_time) values(:user_id, current_date::timestamp + '3days')"
        return self.execute(sql, user_id=user_id)

    def sign_out_off(self, user_id: str):
        sql = "delete from sign_out_users where user_id=:user_id"
        return self.execute(sql, user_id=user_id)

    def get_level(self, user_id: str) -> Optional[User]:
        sql = 'select vip_deadline, block_deadline from users where id=:user_id'
        return self.execute(sql, user_id=user_id)

    def set_black(self, user_id: str, black_id: int):
        sql = ('insert into black_list (user_id, black_id, update_time) '
               'values(:user_id, :black_id, current_timestamp) '
               'on conflict(user_id, black_id) do update set update_time=current_timestamp')
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def unset_black(self, user_id: str, black_id: int):
        sql = 'delete from black_list where user_id=:user_id and black_id=:black_id'
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def black_list(self, user_id: str) -> List[User]:
        sql = ('select u.id, u.nickname from black_list b inner join users u '
               'on b.black_id=u.id where b.user_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def exist(self, user_id: str) -> Optional[int]:
        sql = 'select 1 from users where id=:user_id'
        return self.execute(sql, user_id=user_id)

    def exist_black_list(self, user_id: str, black_id: int) -> Optional[int]:
        sql = ('select exists (select 1 from black_list where user_id=:user_id and black_id=:black_id) '
               'or not exists(select 1 from users where id=:user_id)')
        return self.execute(sql, user_id=user_id, black_id=black_id)

    def wechat_exist(self, open_id: str) -> Optional[str]:
        sql = "select id from third_users where login_type='wechat' and open_id=:open_id"
        return self.execute(sql, open_id=open_id)

    def third_part_sigh_up_third(self, login_type: str, open_id: str, access_token: str) -> int:
        sql = ('insert into third_users (id, login_type, open_id, access_token) values'
               f"(gen_random_uuid(), :login_type, :open_id, :access_token) returning id")
        return self.execute(sql, login_type=login_type, open_id=open_id, access_token=access_token)

    def third_part_sigh_up_user(self, user_id: str) -> int:
        sql = ('insert into users (id, nickname, signature, create_time, vip_deadline, block_deadline, '
               'alive_deadline) values'
               f"(:user_id, :nickname, '说点想说的吧！', current_timestamp, '{vip_deadline}', '-infinity', current_timestamp) "
               "returning id")
        return self.execute(sql, user_id=user_id, nickname=ran_nickname())

    def set_userinfo(self, user_id: str, info: dict):
        settings = ','.join(f"{k}=:{k}" for k, v in info.items() if v is not None)
        sql = (f'update users set {settings} '
               'where id=:user_id')
        return self.execute(sql, user_id=user_id, **info)


dao = UserDao()
