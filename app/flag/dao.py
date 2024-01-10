from typing import List, Optional, Tuple
from uuid import UUID

from app.base_dao import Dao
from app.base_typedef import point, LOCATION
from app.flag.typedef import Flag, GetFlagByMap, CommentResp, UpdateFlag, FlagRegion, FavFlag, OpenFlag, \
    AddFlag, GetFlagByUser, FlagPictures


class FlagDao(Dao):
    fields = (f"f.id, f.user_id, {Dao.location('f.location', 'location')}, f.name, f.content, "
              f'f.user_class, f.type, f.create_time, f.update_time, dead_line, '
              'pictures, status, ico_name ')
    not_hide = 'status&1=0 and (dead_line is null or dead_line > now())'
    anonymous = 'status&0b10=0b10'

    def upload_pictures(self, flag_id: UUID, pictures: List[str]):
        sql = 'update flag set pictures=:pictures where id=:flag_id'
        self.execute(sql, flag_id=flag_id, pictures=pictures)

    def add(self, flag: AddFlag, user_class: int) -> Optional[FlagPictures]:
        sql = ('insert into flag '
               '(id, user_id, location, name, content, user_class, type, status, create_time, update_time, pictures,'
               'ico_name, dead_line) '
               'values(gen_random_uuid(), :user_id, :location, :name, :content, :user_class, :type, :status, '
               'current_timestamp, current_timestamp, array[]::text[], :ico_name, :dead_line) returning id, pictures')
        return self.execute(sql, user_id=flag.user_id, content=flag.content, status=flag.status, name=flag.name,
                            user_class=user_class, location=point(flag.location), type=flag.type,
                            ico_name=flag.ico_name, dead_line=flag.dead_line)

    def update(self, user_id: UUID, flag: UpdateFlag) -> Optional[FlagPictures]:
        sql = ('update flag set name=:name, content=:content, type=:type, status=:status, '
               'ico_name=:ico_name, pictures=:pictures '
               'where id=:id and user_id=:user_id returning id, pictures')
        return self.execute(sql, id=flag.id, user_id=user_id, name=flag.name, content=flag.content, type=flag.type,
                            status=flag.status, ico_name=flag.ico_name, pictures=flag.pictures)

    def get_flag_by_flag(self, flag_id: UUID, user_id: UUID) -> Optional[Flag]:
        sql = f'select {self.fields} from flag f where id=:flag_id and ({self.not_hide} or user_id=:user_id)'
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: Optional[UUID], private_id: UUID, get: GetFlagByUser) -> List[Flag]:
        if user_id:
            condition = f' {self.not_hide} and not {self.anonymous} and user_id=:user_id '
        else:
            condition = ' user_id=:private_id '
        sql = f'select {self.fields} from flag f where {condition} order by {get.order_by}'
        return self.execute(sql, user_id=user_id, private_id=private_id)

    '''
    with s as(
-- 市本级
select a.code from adcode a inner join fences f on a.adcode=f.adcode 
where a."rank" =2 and ST_Contains(f.fence,ST_GeomFromText('point(120.21200999999996 30.20840000000001)', 4326))
),
s0 as(
-- 根据所在市查找下属区县
select a.adcode, a.name, a.rank, a.center from s inner join adcode a on s.code=a.parent 
),
s1 as (
-- 下属曲线的电子围栏
select s0.name, f.fence from s0 inner join fences f on s0.adcode=f.adcode 
where s0.rank=3 and s0.center is not null
),
s2 as (
-- 电子围栏和标记关联
select id, user_id, 
location, 
name, content, user_class, type, create_time, update_time, pictures, is_open, ico_name  
from flag where 
ST_Distance(ST_GeographyFromText('point (120.21200999999996 30.20840000000001  )'), 
ST_GeographyFromText(ST_AsText(location)))<100000
)
select s2.*, s1.name from s2 inner join s1 on ST_Contains(s1.fence,s2.location);
    '''

    def get_flag_by_map(self, user_id: UUID, get: GetFlagByMap) -> List[OpenFlag]:
        sql = (f'select {self.fields}, u.id user_id, u.nickname, u.avatar_name from flag f inner join users u '
               f'on f.user_id=u.id where '
               f'(user_id=:user_id or {self.not_hide}) and type=:type '
               "and ST_Distance(ST_GeographyFromText(:location), "
               'ST_GeographyFromText(ST_AsText(f.location)))<:distance')
        return self.execute(sql, user_id=user_id, type=get.type, location=point(get.location), distance=get.distance)

    def get_city_by_location(self, location: LOCATION) -> Optional[int]:
        sql = ('select a.code from adcode a inner join fences f on a.adcode=f.adcode '
               'where a.rank=2 and ST_Contains(f.fence,ST_GeomFromText(:location))')
        return self.execute(sql, location=point(location))

    def get_flag_by_city(self, user_id: UUID, code, get: GetFlagByMap) -> List[FlagRegion]:
        sql = ('with s0 as( '
               '\n-- 根据所在市查找下属区县\n'
               'select a.adcode, a.name, a.rank, a.center from adcode a where parent=:code), '
               's1 as ( '
               '\n-- 下属区县的电子围栏\n'
               'select s0.name region_name, center, f.fence from s0 inner join fences f on s0.adcode=f.adcode '
               'where s0.rank=3 and s0.center is not null), '
               's2 as ('
               '\n-- 电子围栏和标记关联\n'
               f'select location '
               'from flag where '
               f'(user_id=:user_id or {self.not_hide}) and type=:type) '
               f"select count(location) flag_num, s1.region_name, {Dao.location('s1.center', 'location')} "
               'from s1 left join s2 on ST_Contains(s1.fence,s2.location) '
               f'group by s1.region_name, s1.center')
        return self.execute(sql, user_id=user_id, code=code, type=get.type)

    def set_flag_type(self, user_id: UUID, flag_id: UUID, flag_type: int):
        sql = 'update flag set type=:flag_type where id=:flag_id and user_id=:user_id'
        self.execute(sql, user_id=user_id, flag_id=flag_id, flag_type=flag_type)

    def delete(self, user_id: UUID, flag_id: UUID) -> Optional[str]:
        sql = 'delete from flag where user_id=:user_id and id=:flag_id returning id'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def get_fav(self, user_id: UUID) -> List[FavFlag]:
        sql = (f"select f.id, case when f.{self.anonymous} then null else f.user_id end user_id, "
               f"{Dao.location('location')}, name, content, type, user_class, update_time, ico_name, "
               'pictures, dead_line from fav left join flag f on fav.flag_id=f.id '
               f'where fav.user_id=:user_id and ({self.not_hide} or f.user_id=:user_id)')
        return self.execute(sql, user_id=user_id)

    def add_fav(self, user_id: UUID, flag_id: UUID):
        sql = ('insert into fav (user_id, flag_id, create_time)'
               'values(:user_id,:flag_id,current_timestamp)')
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def delete_fav(self, user_id: UUID, flag_id: UUID) -> Optional[str]:
        sql = 'delete from fav where user_id=:user_id and flag_id=:flag_id returning flag_id'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def flag_exist(self, user_id: UUID, flag_id: UUID) -> Optional[int]:
        sql = ('select 1 from flag f inner join users u on '
               f'f.user_id=u.id where (f.user_id=:user_id or f.{self.not_hide}) and f.id=:flag_id')
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
               f'on c.flag_id=f.id where (f.user_id=:user_id or f.{self.not_hide}) and f.id=:flag_id '
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

    def flag_is_open(self, user_id: UUID, flag_id: UUID) -> int:
        sql = f'select exists(select 1 from flag where id=:flag_id and ({self.not_hide} or user_id=:user_id))'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)


dao: FlagDao = FlagDao()
