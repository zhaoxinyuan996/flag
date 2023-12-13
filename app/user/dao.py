from datetime import datetime
from typing import Tuple, Optional, List
from app.user.typedef import User
from util.database import Dao


class UserDao(Dao):
    def sign_up(self, username: str, password: str) -> int:
        sql = ('insert into users (username, password, create_time, vip_deadline, block_deadline) '
               "values(:username, :password, current_timestamp, 'infinity', '-infinity') returning id")
        return self.execute(sql, username=username, password=password)

    def sign_in(self, username: str) -> Optional[Tuple[int, str]]:
        sql = 'select id, password from users where username=:username'
        return self.execute(sql, username=username)

    def user_info(self, user_id: int) -> Optional[User]:
        sql = ('select id, username, nickname, profile_picture, signature, vip_deadline, block_deadline '
               'from users where id=:user_id')
        return self.execute(sql, user_id=user_id)

    def set_profile_picture(self, user_id: int, url: str):
        sql = 'update users set profile_picture=:url where id=:user_id'
        return self.execute(sql, user_id=user_id, url=url)

    def set_user_nickname(self, user_id: int, nickname: str):
        sql = 'update users set nickname=:nickname where id=:user_id'
        return self.execute(sql, user_id=user_id, nickname=nickname)

    def set_user_signature(self, user_id: int, signature: str):
        sql = 'update users set signature=:signature where id=:user_id'
        return self.execute(sql, user_id=user_id, signature=signature)

    def follow_add(self, fans_id: int, star_id: int):
        sql = 'insert into follow (fans_id ,star_id) values(:fans_id, :star_id)'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_remove(self, fans_id: int, star_id: int):
        sql = 'delete from where fans_id=:fans_id, star_id=:star_id'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_star(self, user_id: int) -> List[User]:
        sql = ('select u.id, u.nickname, u.username, u.signature from follow f inner join users u '
               'on f.star_id=u.id where f.fans_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def follow_fans(self, user_id: int) -> List[User]:
        sql = ('select u.id, u.nickname, u.username, u.signature from follow f inner join users u '
               'on f.fans_id=u.id where f.star_id=:user_id')
        return self.execute(sql, user_id=user_id)

    def sign_out(self, user_id: int):
        sql = "insert into sign_out_users (user_id, out_time) values(:user_id, current_date::timestamp + '3days')"
        return self.execute(sql, user_id=user_id)

    def sign_out_off(self, user_id: int):
        sql = "delete from sign_out_users where user_id=:user_id"
        return self.execute(sql, user_id=user_id)

    def get_level(self, user_id: int) -> User:
        sql = 'select vip_deadline, block_deadline from users where id=:user_id'
        return self.execute(sql, user_id=user_id)


dao = UserDao()
