from typing import Tuple, Optional
from app.user.typedef import User
from util.database import Dao


class UserDao(Dao):
    def sign_up(self, username: str, password: str) -> int:
        sql = ('insert into users (username, password, create_time, vip_deadline)'
               ' values(:username, :password, current_timestamp, :infinity) returning id')
        return self.execute(sql, username=username, password=password, infinity='infinity')

    def sign_in(self, username: str) -> Optional[Tuple[int, str]]:
        sql = 'select id, password from users where username=:username'
        return self.execute(sql, username=username)

    def user_info(self, user_id: int) -> User:
        sql = ('select id, username, nickname, signature, vip_deadline'
               ' from users where id=:user_id')
        return self.execute(sql, user_id=user_id)

    def set_user_nickname(self, user_id: int, nickname: str):
        sql = 'update users set nickname=:nickname where id=:user_id'
        return self.execute(sql, user_id=user_id, nickname=nickname)

    def set_user_signature(self, user_id: int, signature: str):
        sql = 'update users set signature=:signature where id=:user_id'
        return self.execute(sql, user_id=user_id, signature=signature)


dao = UserDao()
