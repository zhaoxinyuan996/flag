from typing import List

from util.database import Dao
from .typedef import Test


class TestDao(Dao):
    def test(self) -> List[Test]:
        return self.execute('select * from test')


dao = TestDao()
