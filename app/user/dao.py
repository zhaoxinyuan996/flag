from typing import Tuple, Optional, List
from app.user.typedef import User
from util.database import Dao


vip_deadline = 'infinity'


class UserDao(Dao):
    def sign_up(self, username: str, password: str, nickname: str) -> int:
        sql = ('insert into users (username, password, nickname, create_time, vip_deadline, block_deadline, '
               'alive_deadline) values(:username, :password, :nickname, current_timestamp, '
               f"{vip_deadline}', '-infinity', current_timestamp) "
               "returning id")
        return self.execute(sql, username=username, password=password, nickname=nickname)

    def sign_in(self, username: str) -> Optional[Tuple[int, str]]:
        sql = 'select id, password from users where username=:username'
        return self.execute(sql, username=username)

    def user_info(self, user_id: str) -> Optional[User]:
        sql = ('select id, username, nickname, profile_picture, signature, '
               f"'{vip_deadline}', block_deadline, belong, location_x, location_y "
               'from users where id=:user_id')
        return self.execute(sql, user_id=user_id)

    def refresh(self, user_id: str, location_x: float, location_y: float):
        sql = ('update users set alive_deadline=current_timestamp, location_x=:location_x, location_y=:location_y '
               'where id=:user_id')
        return self.execute(sql, user_id=user_id, location_x=location_x, location_y=location_y)

    def set_profile_picture(self, user_id: str, url: str):
        sql = 'update users set profile_picture=:url where id=:user_id'
        return self.execute(sql, user_id=user_id, url=url)

    def set_user_nickname(self, user_id: str, nickname: str):
        sql = 'update users set nickname=:nickname where id=:user_id'
        return self.execute(sql, user_id=user_id, nickname=nickname)

    def set_user_signature(self, user_id: str, signature: str):
        sql = 'update users set signature=:signature where id=:user_id'
        return self.execute(sql, user_id=user_id, signature=signature)

    def follow_add(self, fans_id: int, star_id: int):
        sql = 'insert into follow (fans_id ,star_id) values(:fans_id, :star_id)'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_remove(self, fans_id: int, star_id: int):
        sql = 'delete from follow where fans_id=:fans_id and star_id=:star_id'
        return self.execute(sql, fans_id=fans_id, star_id=star_id)

    def follow_star(self, user_id: str) -> List[User]:
        sql = ('select u.id, u.nickname, u.username, u.signature from follow f inner join users u '
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
               'on b.user_id=u.id where u.id=:user_id')
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

    def third_part_sigh_up_user(self, user_id: str, nickname: str) -> int:
        sql = ('insert into users (id, nickname, create_time, vip_deadline, block_deadline, '
               'alive_deadline) values'
               f"(:user_id, :nickname, current_timestamp, '{vip_deadline}', '-infinity', current_timestamp) "
               "returning id")
        return self.execute(sql, user_id=user_id, nickname=nickname)


dao = UserDao()
