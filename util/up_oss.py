import logging
import random
import string
from upyun import upyun, UpYunServiceException
from util.config import up_config
string_pool = string.ascii_letters + string.digits

log = logging.getLogger(__name__)


class UpOss:
    host = 'cdn.flag-app.asia'
    service = 'flag-app'

    def __init__(self):
        self.client = upyun.UpYun(
            self.service,
            up_config['username'],
            up_config['password'],
            endpoint=upyun.ED_AUTO)

    @staticmethod
    def random_str():
        return ''.join(random.sample(string_pool, 10))

    def upload(self, bucket: str, filename: str, b: bytes):
        """上传"""
        self.client.put(f'/{bucket}/{filename}', b)

    def delete(self, bucket: str, filename: str, not_exist_ignore=True):
        """删除"""
        try:
            self.client.delete(f'/{bucket}/{filename}')
        except UpYunServiceException as e:
            log.error(f'up delete: {e}')
            # 404忽略
            if e.status == 404 and not_exist_ignore:
                return
            raise e

    def get_url(self, bucket: str, filename: str):
        return f'{self.host}/{bucket}{filename}'


up_oss: UpOss = UpOss()


if __name__ == '__main__':
    emoji = up_oss.client.getlist('/emoji-ms-64')
    print(emoji)
    # import os
    # folder = '/emoji-ms-64/'
    # for i in os.listdir(r'C:\Users\11782\Desktop\fluentui-emoji-main\64'):
    #     with open(r'C:\Users\11782\Desktop\fluentui-emoji-main\64' + '\\' + i, 'rb') as f:
    #         up_oss.client.put(folder + i, f.read())
