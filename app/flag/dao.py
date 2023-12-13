from typing import Tuple, Optional, List
from app.flag.typedef import Flag
from util.database import Dao


class FlagDao(Dao):
    def add(self, flag: Flag) -> int:
        sql = ('insert into flag (user_id, location, content, is_open, create_time, update_time, has_picture) '
               'values(:user_id, POINT(:location_x, :location_y), :content, :is_open, '
               'current_timestamp, current_timestamp, :has_picture) returning id')
        return self.execute(sql, user_id=flag.user_id, content=flag.content,
                            is_open=flag.is_open, has_picture=flag.has_picture,
                            location_x=flag.location[0], location_y=flag.location[1])


dao = FlagDao()
