from typing import List

from .typedef import Test
from ..base_dao import Dao


class TestDao(Dao):
    def test(self) -> List[Test]:
        return self.execute('select * from test')


dao = TestDao()
