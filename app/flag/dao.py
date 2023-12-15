from typing import List, Optional, Tuple
from app.flag.typedef import Flag, GetFlagBy, GetFlagByWithType, Comment, CommentResp
from util.database import Dao


class FlagDao(Dao):
    fields = 'id, user_id, location_x, location_y, content, type, create_time, pictures, is_open'

    def add(self, flag: Flag) -> int:
        sql = ('insert into flag '
               '(user_id, location_x, location_y, content, type, is_open, create_time, update_time, pictures) '
               'values(:user_id, :location_x, :location_y, :content, :type, :is_open, '
               'current_timestamp, current_timestamp, array[]::text[]) returning id')
        return self.execute(sql, user_id=flag.user_id, content=flag.content, is_open=flag.is_open,
                            location_x=flag.location[0], location_y=flag.location[1], type=flag.type)

    def update(self, flag: Flag) -> Optional[int]:
        sql = 'update flag set pictures=:pictures where id=:id returning id'
        return self.execute(sql, id=flag.id, pictures=flag.pictures)

    def get_flag_by_flag(self, flag_id: int, user_id: int) -> Optional[Flag]:
        sql = f'select {self.fields} from flag where id=:flag_id and (is_open=1 or user_id=:user_id)'
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: int, private_id: int, get: GetFlagBy) -> List[Flag]:
        sql = (f'select {self.fields} from flag where '
               'user_id=:private_id or (is_open=1 and user_id=:user_id) '
               f'order by {get.order} {get.asc}')
        return self.execute(sql, user_id=user_id, private_id=private_id)

    def get_flag_by_location(self, user_id: int, get: GetFlagByWithType) -> List[Flag]:
        sql = (f'select {self.fields} from flag where '
               '(user_id=:user_id or is_open=1) and type=:type and '
               'location_x<:location_x_add and location_x>:location_x_sub and '
               'location_y<:location_y_add and location_y>:location_y_sub '
               f'order by {get.order} {get.asc}')
        return self.execute(sql, user_id=user_id, type=get.type,
                            location_x_add=get.key[0] + get.distance[0],
                            location_x_sub=get.key[0] - get.distance[0],
                            location_y_add=get.key[1] + get.distance[1],
                            location_y_sub=get.key[1] - get.distance[1],
                            )

    def get_flag_by_location_count(self, user_id: int, get: GetFlagByWithType) -> int:
        sql = (f'select count(1) from flag where '
               '(user_id=:user_id or is_open=1) and type=:type and '
               'location_x<:location_x_add and location_x>:location_x_sub and '
               'location_y<:location_y_add and location_y>:location_y_sub ')
        return self.execute(sql, user_id=user_id, type=get.type,
                            location_x_add=get.key[0] + get.distance[0],
                            location_x_sub=get.key[0] - get.distance[0],
                            location_y_add=get.key[1] + get.distance[1],
                            location_y_sub=get.key[1] - get.distance[1],
                            )

    def set_flag_type(self, user_id: int, flag_id: int, flag_type: int):
        sql = 'update flag set type=:flag_type where id=:flag_id and user_id=:user_id'
        self.execute(sql, user_id=user_id, flag_id=flag_id, flag_type=flag_type)

    def add_comment(self, flag_id: int, user_id: str, content: str,
                    location: Tuple[float, float], root_comment_id: Optional[int], prefix: str):
        prefix = prefix or ''
        sql = ('insert into flag_comment (flag_id, user_id, content, root_comment_id, '
               'location_x, location_y, prefix, comment_time) values('
               ':flag_id, :user_id, :content, :root_comment_id, :location_x, :location_y, :prefix, current_timestamp)')
        return self.execute(sql, flag_id=flag_id, user_id=user_id, content=content, location_x=location[0],
                            location_y=location[1], root_comment_id=root_comment_id, prefix=prefix)

    def add_sub_comment(self, root_comment_id: int):
        sql = 'update flag_comment set comment_time=current_timestamp where id=:root_comment_id'
        self.execute(sql, root_comment_id=root_comment_id)

    def get_nickname_by_comment_id(self, root_comment_id: int) -> Optional[str]:
        sql = ('select nickname from flag_comment c inner join users u on c.user_id=u.id '
               'where root_comment_id=:root_comment_id')
        return self.execute(sql, root_comment_id=root_comment_id)

    def get_comment(self, flag_id: int, user_id: int) -> List[CommentResp]:
        sql = (
            'with s1 as (select id, user_id, content, root_comment_id, prefix, comment_time from flag_comment where flag_id=1), '
            's2 as (select u.nickname, u.profile_picture, s1.id, user_id, content, prefix, comment_time from s1 inner join users u on s1.user_id=u.id where root_comment_id is null), '
            's3 as (select u.nickname, u.profile_picture, s1.id, user_id, content, prefix, comment_time, root_comment_id from s1 inner join users u on s1.user_id=u.id where root_comment_id is not null), '
            's4 as (select s2.nickname, s2.profile_picture, s2.id, s2.user_id, s2.content, s2.prefix, s2.comment_time, '
            's3.nickname s_nickname, s3.profile_picture s_profile_picture, s3.id s_id, s3.user_id s_user_id, s3.content s_content, s3.prefix s_prefix, s3.comment_time s_comment_time from s2 left join s3 on s2.id=s3.root_comment_id) '
            'select max(nickname) nickname, max(profile_picture) profile_picture, id, max(user_id) user_id, max(content) content, max(prefix) prefix, max(comment_time) comment_time, '
            'case when max(s_id) is null then array[]::json[] else '
            "array_agg(json_build_object('nickname', s_nickname, 'profile_picture', s_profile_picture, 'id', s_id, 'user_id', s_user_id, 'content', s_content, 'prefix', s_prefix, 'comment_time', s_comment_time) order by comment_time desc) end sub_comment "
            'from s4 group by id order by comment_time desc;')
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def delete_comment(self, comment_id: int, user_id: int):
        sql = 'delete from comment where (id=:comment_id or root_comment_id=:comment_id) and user_id=:user_id'
        self.execute(sql, comment_id=comment_id, user_id=user_id)

    def flag_is_open(self, user_id: int, flag_id: int) -> int:
        sql = 'select exists(select 1 from flag where id=:flag_id and (is_open=1 or user_id=:user_id))'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)


dao = FlagDao()
