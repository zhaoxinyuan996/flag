from typing import List, Optional, Any
from uuid import UUID
from app.base_dao import Dao
from app.base_typedef import point, LOCATION
from app.flag.typedef import GetFlagByMap, CommentResp, UpdateFlag, FlagRegion, OpenFlag, \
    AddFlag, GetFlagByUser, FlagPictures, AddComment, DeleteComment


class FlagDao(Dao):
    fields = (f"f.id, f.user_id, {Dao.location('f.location', 'location')}, f.name, f.content, "
              f'f.user_class, f.type, f.create_time, f.update_time, dead_line, '
              'pictures, status, ico_name ')
    not_hide = 'status&1=0 and (dead_line is null or dead_line > now())'
    anonymous = 'status&0b10=0b10'

    def upload_pictures(self, user_id: UUID, flag_id: UUID, pictures: List[str]):
        sql = 'update flag set pictures=:pictures where id=:flag_id and user_id=:user_id'
        self.execute(sql, user_id=user_id, flag_id=flag_id, pictures=pictures)

    def get_pictures(self, user_id: UUID, flag_id: UUID) -> Optional[Any]:
        sql = 'select pictures from flag where id=:flag_id and user_id=:user_id'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def add(self, user_id: UUID, flag: AddFlag, user_class: int) -> Optional[FlagPictures]:
        sql = ('insert into flag '
               '(id, user_id, location, name, content, user_class, type, status, create_time, update_time, pictures,'
               'ico_name, dead_line) '
               'values(gen_random_uuid(), :user_id, :location, :name, :content, :user_class, :type, :status, '
               'current_timestamp, current_timestamp, array[]::text[], :ico_name, :dead_line) returning id, pictures')
        return self.execute(sql, user_id=user_id, content=flag.content, status=flag.status, name=flag.name,
                            user_class=user_class, location=point(flag.location), type=flag.type,
                            ico_name=flag.ico_name, dead_line=flag.dead_line)

    def update(self, user_id: UUID, flag: UpdateFlag) -> Optional[FlagPictures]:
        sql = ('update flag set name=:name, content=:content, type=:type, status=:status, '
               'ico_name=:ico_name, update_time=current_timestamp '
               'where id=:id and user_id=:user_id returning id, pictures')
        return self.execute(sql, id=flag.id, user_id=user_id, name=flag.name, content=flag.content, type=flag.type,
                            status=flag.status, ico_name=flag.ico_name)

    def get_flag_by_flag(self, user_id: UUID, flag_id: UUID) -> Optional[OpenFlag]:
        condition = f'(({self.not_hide} and not {self.anonymous}) or user_id=:user_id) '
        sql = (f'select {self.fields}, '
               f"exist(like_users, '{user_id}') is_like, exist(fav_users, '{user_id}') is_fav, "
               f'like_num, fav_num, comment_num '
               f'from flag f inner join flag_statistics s on f.id=s.flag_id '
               f'where f.id=:flag_id and {condition} and s.flag_id=:flag_id')
        print(self.text(sql, flag_id=flag_id, user_id=user_id))
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: Optional[UUID], private_id: UUID, get: GetFlagByUser) -> List[OpenFlag]:
        if user_id:
            condition = f' {self.not_hide} and not {self.anonymous} and user_id=:user_id '
        else:
            condition = ' user_id=:private_id '
        sql = (f'select {self.fields}, '
               f"exist(like_users, '{private_id}') is_like, exist(fav_users, '{private_id}') is_fav, "
               f'like_num, fav_num, comment_num '
               f'from flag f inner join flag_statistics s on f.id=s.flag_id '
               f'where {condition} order by {get.order_by}')
        print(self.text(sql, user_id=user_id, private_id=private_id))
        return self.execute(sql, user_id=user_id, private_id=private_id)

    def get_flag_by_map(self, user_id: UUID, get: GetFlagByMap) -> List[OpenFlag]:
        condition = f'(({self.not_hide} and not {self.anonymous}) or user_id=:user_id) '
        sql = (f'select {self.fields}, u.id user_id, u.nickname, u.avatar_name, '
               f"exist(like_users, '{user_id}') is_like, exist(fav_users, '{user_id}') is_fav, "
               f'like_num, fav_num, comment_num '
               f'from flag f inner join users u on f.user_id=u.id '
               f'inner join flag_statistics s on f.id=s.flag_id '
               f'where {condition} and type=:type '
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

    def delete(self, user_id: UUID, flag_id: UUID) -> Optional[FlagPictures]:
        sql = 'delete from flag where user_id=:user_id and id=:flag_id returning id, pictures'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def is_like(self, user_id: UUID, flag_id: UUID) -> Optional[bool]:
        sql = f'select exist(like_users, {user_id}) where flag_id=:flag_id'
        return self.execute(sql, flag_id=flag_id)

    def get_fav(self, user_id: UUID) -> List[OpenFlag]:
        sql = (f'select {self.fields}, '
               f"exist(like_users, '{user_id}') is_like, exist(fav_users, '{user_id}') is_fav, "
               f'like_num, fav_num, comment_num '
               f'from fav left join flag f on fav.flag_id=f.id '
               'left join flag_statistics s on fav.flag_id=s.flag_id '
               f'where fav.user_id=:user_id and ({self.not_hide} or f.user_id=:user_id) order by fav.create_time')
        return self.execute(sql, user_id=user_id)

    def add_fav(self, user_id: UUID, flag_id: UUID) -> Optional[UUID]:
        sql = ('insert into fav (user_id, flag_id, create_time)'
               'values(:user_id,:flag_id,current_timestamp) returning flag_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def delete_fav(self, user_id: UUID, flag_id: UUID) -> Optional[UUID]:
        sql = 'delete from fav where user_id=:user_id and flag_id=:flag_id returning flag_id'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def flag_exist(self, user_id: UUID, flag_id: UUID) -> Optional[int]:
        sql = ('select 1 from flag f inner join users u on '
               f'f.user_id=u.id where (f.user_id=:user_id or f.{self.not_hide}) and f.id=:flag_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def get_comment_distance(self, user_id: UUID, flag_id: UUID, location: LOCATION) -> Optional[int]:
        sql = ('select ST_Distance(location, :location) from flag f where id=:flag_id '
               f'and (f.user_id=:user_id or f.{self.not_hide}) and not {self.anonymous}')
        return self.execute(sql, user_id=user_id, flag_id=flag_id, location=point(location))

    def add_comment(self, user_id: UUID, add: AddComment, distance) -> int:
        sql = ('insert into flag_comment (flag_id, user_id, content, parent_id, '
               'like_num, distance, create_time) values( '
               ':flag_id, :user_id, :content, :parent_id, 0, :distance, '
               'current_timestamp) returning id')
        return self.execute(sql, flag_id=add.flag_id, user_id=user_id, content=add.content,
                            location=point(add.location), parent_id=add.parent_id, distance=distance)

    def get_nickname_by_comment_id(self, user_id: UUID, flag_id: UUID, parent_id: int) -> Optional[str]:
        sql = ('with s1 as (select c.user_id from flag_comment c inner join flag f '
               f'on c.flag_id=f.id where (f.user_id=:user_id or f.{self.not_hide}) and f.id=:flag_id '
               'and c.id=:parent_id and c.parent_id is null) select u.nickname from users u inner join s1 '
               'on u.id=s1.user_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id, parent_id=parent_id)

    def get_comment(self, user_id: UUID, flag_id: UUID) -> List[CommentResp]:
        sql = ('select u.id=:user_id owner, u.id user_id, u.avatar_name, u.nickname, '
               'c.id, c.like_num, c.content, c.parent_id, c.distance, c.create_time from flag_comment c '
               'inner join users u on c.user_id=u.id where c.flag_id=:flag_id')
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def delete_comment(self, user_id: UUID, comment_id: int) -> Optional[DeleteComment]:
        sql = ('delete from flag_comment where (id=:comment_id or parent_id=:comment_id) and user_id=:user_id '
               'returning parent_id')
        return self.execute(sql, comment_id=comment_id, user_id=user_id)

    def flag_is_open(self, user_id: UUID, flag_id: UUID) -> int:
        sql = f'select exists(select 1 from flag where id=:flag_id and ({self.not_hide} or user_id=:user_id))'
        return self.execute(sql, user_id=user_id, flag_id=flag_id)

    def insert_statistics(self, flag_id: UUID):
        sql = ('insert into flag_statistics (flag_id, like_users, fav_users, comment_users, update_time) '
               'values(:flag_id, null, null, null, current_timestamp)')
        self.execute(sql, flag_id=flag_id)

    def delete_statistics(self, flag_id: UUID):
        """flag_id只能是接口返回值，防止接口注入，因为没有限定user_id"""
        sql = 'delete from flag_statistics where flag_id=:flag_id'
        self.execute(sql, flag_id=flag_id)

    def set_statistics(self,
                       flag_id: UUID,
                       like_users_up: List[UUID] = (),
                       like_users_down: List[UUID] = (),
                       fav_users_up: List[UUID] = (),
                       fav_users_down: List[UUID] = (),
                       comment_users_up: List[UUID] = (),
                       comment_users_down: List[UUID] = (),
                       ):
        loop = []
        for uuid in like_users_up:
            loop.append(f" like_users['{uuid}']=current_timestamp::text ")
        for uuid in like_users_down:
            loop.append(f''' like_users = delete(like_users, '{uuid}') ''')
        for uuid in fav_users_up:
            loop.append(f" fav_users['{uuid}']=current_timestamp::text ")
        for uuid in fav_users_down:
            loop.append(f''' fav_users = delete(fav_users, '{uuid}') ''')
        for uuid in comment_users_up:
            loop.append(f" comment_users['{uuid}']=current_timestamp::text ")
        for uuid in comment_users_down:
            loop.append(f''' comment_users = delete(comment_users, '{uuid}') ''')
        like_diff = len(like_users_up) - len(like_users_down)
        fav_diff = len(fav_users_up) - len(fav_users_down)
        comment_diff = len(comment_users_up) - len(comment_users_down)
        sql = (f"update flag_statistics set {','.join(loop)} "
               f", like_num={like_diff}+like_num "
               f", fav_num={fav_diff}+fav_num "
               f", comment_num={comment_diff}+comment_num "
               f"where flag_id=:flag_id")
        print(sql)
        self.execute(sql, flag_id=flag_id)


dao: FlagDao = FlagDao()
