from typing import List, Optional
from app.flag.typedef import Flag
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

    def update(self, flag: Flag):
        sql = 'update flag set pictures=:pictures where id=:id'
        self.execute(sql, id=flag.id, pictures=flag.pictures)

    def get_flag_by_flag(self, flag_id: int, user_id: int) -> Optional[Flag]:
        sql = f'select {self.fields} from flag where id=:flag_id and (is_open=1 or user_id=:user_id)'
        return self.execute(sql, flag_id=flag_id, user_id=user_id)

    def get_flag_by_user(self, user_id: int, private_id: int, _order: str, _asc: int) -> List[Flag]:
        order = 'create_time' if _order == 't' else 'create_time'
        asc = 'asc' if _asc else 'desc'
        sql = (f'select {self.fields} from flag where '
               'user_id=:private_id or (is_open=1 and user_id=:user_id) '
               f'order by {order} {asc}')
        return self.execute(sql, user_id=user_id, private_id=private_id)

    def get_flag_by_location(self, user_id: int) -> List[Flag]:
        ...

    def get_flag_by_location_count(self, user_id: int) -> Optional[int]:
        ...


dao = FlagDao()
