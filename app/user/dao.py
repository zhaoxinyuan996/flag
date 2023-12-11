from util.database import Dao


class UserDao(Dao):
    def sign_up_0_1(self, username: str, password: str) -> int:
        sql = "insert into users (username, password) values('%s', '%s') returning id" % (username, password)
        return self.execute(sql)


dao = UserDao()
