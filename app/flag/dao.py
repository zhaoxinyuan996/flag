from typing import List, Optional, Tuple
from uuid import UUID

from app.base_dao import Dao
from app.base_typedef import point
from app.flag.typedef import Flag, GetFlagBy, GetFlagByMap, CommentResp, GetFlagByMapCount, UpdateFlag


class FlagDao(Dao):
    fields = (f"id, user_id, {Dao.location('location')}, name, content, user_class, type, create_time, update_time, "
              'pictures, is_open, ico_name ')

    def add(self, flag: Flag, user_class: int) -> str:
        sql = ('insert into flag '
               '(id, user_id, location, name, content, user_class, type, is_open, create_time, update_time, pictures,'
               'ico_name) '
               'values(gen_random_uuid(), :user_id, :location, :name, :content, :user_class, :type, :is_open, '
               'current_timestamp, current_timestamp, array[]::text[], :ico_name) returning id')
        return self.execute(sql, user_id=flag.user_id, content=flag.content, is_open=flag.is_open, name=flag.name,
                            user_class=user_class, location=point(flag.location), type=flag.type,
                            ico_name=flag.ico_name)

    def update(self, flag: UpdateFlag) -> Optional[int]:
        sql = ('update flag set name=:name, content=:content, type=:type, is_open=:is_open, '
               'ico_name=:ico_name, pictures=:pictures '
               'where id=:id and user_id=:user_id returning id')
        return self.execute(sql, id=flag.id, user_id=flag.user_id, name=flag.name, content=flag.content, type=flag.type,
                            is_open=flag.is_open, ico_name=flag.ico_name, pictures=flag.pictures)

    def get_flag_by_flag(self, flag_id: UUID, user_id: UUID) -> Optional[Flag]:
        sql = f'select {self.fields} from flag where id=:flag_id and (is_open=1 or user_id=:user_id)'
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: Optional[UUID], private_id: UUID, get: GetFlagBy) -> List[Flag]:
        sql = (f'select {self.fields} from flag where user_id=:private_id '
               + (' or (is_open=1 and user_id=:user_id) ' if user_id is not None else '') +
               f'order by {get.order} {get.asc}')
        return self.execute(sql, user_id=user_id, private_id=private_id)

    def get_flag_by_map(self, user_id: UUID, get: GetFlagByMap) -> List[Flag]:
        sql = (f'select {self.fields} from flag where '
               '(user_id=:user_id or is_open=1) '
               + ('and type=:type ' if get.type is not None else '') +
               "and ST_Distance(ST_GeographyFromText(:location), "
               'ST_GeographyFromText(ST_AsText(location)))<:distance')
        return self.execute(sql, user_id=user_id, type=get.type, location=point(get.location), distance=get.distance)

    def get_flag_by_map_count(self, user_id: UUID, get: GetFlagByMapCount) -> int:
        sql = (f'select count(1) from flag where '
               '(user_id=:user_id or is_open=1) and type=:type and '
               "ST_Distance(ST_GeographyFromText(:location), "
               'ST_GeographyFromText(ST_AsText(location)))<:distance')
        return self.execute(sql, user_id=user_id, type=get.type, location=point(get.location), distance=get.distance)

    def set_flag_type(self, user_id: UUID, flag_id: UUID, flag_type: int):
        sql = 'update flag set type=:flag_type where id=:flag_id and user_id=:user_id'
        self.execute(sql, user_id=user_id, flag_id=flag_id, flag_type=flag_type)

    def delete(self, user_id: UUID, flag_id: UUID) -> Optional[str]:
        sql = 'delete from flag where user_id=:user_id and id=:flag_id returning id'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def flag_exist(self, user_id: UUID, flag_id: UUID) -> Optional[int]:
        sql = ('select 1 from flag f inner join users u on '
               'f.user_id=u.id where (f.user_id=:user_id or f.is_open=1) and f.id=:flag_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def root_comment_is_root(self, root_comment_id: int) -> Optional[int]:
        sql = 'select 1 from flag_comment f where id=:root_comment_id and root_comment_id is null'
        return self.execute(sql, root_comment_id=root_comment_id)

    def add_comment(self, flag_id: UUID, user_id: UUID, content: str,
                    location: Tuple[float, float], root_comment_id: Optional[int], prefix: str):
        prefix = prefix or ''
        sql = ('insert into flag_comment (flag_id, user_id, content, root_comment_id, '
               'location, prefix, comment_time) values('
               ':flag_id, :user_id, :content, :root_comment_id, :location, :prefix, current_timestamp)')
        return self.execute(sql, flag_id=flag_id, user_id=user_id, content=content, location=point(location),
                            root_comment_id=root_comment_id, prefix=prefix)

    def get_nickname_by_comment_id(self, user_id: UUID, flag_id: UUID, root_comment_id: int) -> Optional[str]:
        sql = ('with s1 as (select c.user_id from flag_comment c inner join flag f '
               'on c.flag_id=f.id where (f.user_id=:user_id or f.is_open=1) and f.id=:flag_id '
               'and c.id=:root_comment_id and c.root_comment_id is null) select u.nickname from users u inner join s1 '
               'on u.id=s1.user_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id, root_comment_id=root_comment_id)

    # 等客户端做到的时候再改
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
        sql = 'delete from flag_comment where (id=:comment_id or root_comment_id=:comment_id) and user_id=:user_id'
        self.execute(sql, comment_id=comment_id, user_id=user_id)

    def flag_is_open(self, user_id: int, flag_id: int) -> int:
        sql = 'select exists(select 1 from flag where id=:flag_id and (is_open=1 or user_id=:user_id))'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)


dao = FlagDao()
