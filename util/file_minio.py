import logging
import random
import string
from PIL import Image
from io import BytesIO
from datetime import timedelta
from minio import Minio, S3Error
from app.constants import FileType
from util.config import config

minio_config = config['minio'][config['env']]

log = logging.getLogger(__name__)
prefix = 'o-'
string_pool = string.ascii_letters + string.digits


class FileMinio:
    def __init__(self):
        self.client = Minio(
            f'{minio_config["host"]}:{minio_config["port"]}',
            access_key=minio_config['username'],
            secret_key=minio_config['password'],
            secure=False)

    def exists_bucket(self, bucket_name) -> bool:
        return self.client.bucket_exists(bucket_name=bucket_name)

    def create_bucket(self, bucket_name: str) -> bool:
        self.client.make_bucket(bucket_name=bucket_name)
        return True

    def remove_bucket(self, bucket_name) -> bool:
        try:
            self.client.remove_bucket(bucket_name=bucket_name)
        except S3Error as e:
            log.exception(e)
            return False
        return True

    @staticmethod
    def random_str():
        return ''.join(random.sample(string_pool, 10))

    def remove_object(self, filename: str, file_type: str):
        """删除图片，不存在的也不报错，然后filename已经带前缀了，不要再加prefix"""
        filename = filename.rsplit('/', 1)[-1]
        self.client.remove_object(file_type, f'{filename}')

    def upload(self, filename: str, file_type: str, b: bytes):
        io = BytesIO(b)
        self.client.put_object(file_type, f'{prefix}{filename}', io, len(b))

    def get_file_url_limited_time(self, bucket_name: str, filename: str, days=7) -> str:
        return self.client.presigned_get_object(
            bucket_name, f'{prefix}{filename}',
            expires=timedelta(days=days))

    @staticmethod
    def get_file_url(filename: str, bucket_name: str):
        return f'http://{minio_config["host"]}:{minio_config["port"]}/{bucket_name}/{prefix}{filename}'

    @staticmethod
    def thumbnail(src_io: bytes, type_: str):
        """
        https://madmalls.com/blog/post/python3-resize-images/
        将原始图片的宽高比例调整到跟目标图的宽高比例一致，所以需要：
        1. 切图，缩小原始图片的宽度或者高度
        2. 将切图后的新图片生成缩略图
        :param type_: 类型
        :param src_io: 头像处理
        :param src_io: 原始图片的名字
        """
        # 打开原始图片
        src_image = Image.open(BytesIO(src_io))
        # 原始图片的宽度和高度
        src_width, src_height = src_image.size
        if type_ == FileType.head_pic:
            dst_width = dst_height = 120
        else:
            dst_width = int(src_width / 2)
            dst_height = int(src_height / 2)

        # # 原始图片的宽高比例，保留2位小数
        # src_ratio = float('%.2f' % (src_width / src_height))
        # # 目标图片的宽高比例，保留2位小数
        # dst_ratio = float('%.2f' % (dst_width / dst_height))
        #
        # # 如果原始图片的宽高比例大，则将原始图片的宽度缩小
        # if src_ratio >= dst_ratio:
        #     # 切图后的新高度
        #     if src_height < dst_height:
        #         logging.warning('目标图片的高度({0} px)超过原始图片的高度({1} px)，最终图片的高度为 {1} px'.
        #                         format(dst_height, src_height))
        #     new_src_height = src_height
        #     # 切图后的新宽度
        #     new_src_width = int(new_src_height * dst_ratio)  # 向下取整
        #     if new_src_width > src_width:  # 比如原始图片(1280*480)和目标图片(800*300)的比例完全一致时，此时new_src_width=1281，可能四周会有一条黑线
        #         logging.warning('切图的宽度({0} px)超过原始图片的宽度({1} px)，最终图片的宽度为 {1} px'
        #                         .format(new_src_width, src_width))
        #         new_src_width = src_width
        #     blank = int((src_width - new_src_width) / 2)  # 左右两边的空白。向下取整
        #     # 左右两边留出同样的宽度，计算出新的 box: The crop rectangle, as a (left, upper, right, lower)-tuple
        #     box = (blank, 0, blank + new_src_width, new_src_height)
        # # 如果原始图片的宽高比例小，则将原始图片的高度缩小
        # else:
        #     # 切图后的新宽度
        #     if src_width < dst_width:
        #         logging.warning('目标图片的宽度({0} px)超过原始图片的宽度({1} px)，最终图片的宽度为 {1} px'.
        #                         format(dst_width, src_width))
        #     new_src_width = src_width
        #     # 切图后的新高度
        #     new_src_height = int(new_src_width / dst_ratio)  # 向下取整
        #     if new_src_height > src_height:
        #         logging.warning('切图的高度({0} px)超过原始图片的高度({1} px)，最终图片的高度为 {1} px'.
        #                         format(new_src_height, src_height))
        #         new_src_height = src_height
        #     blank = int((src_height - new_src_height) / 2)  # 上下两边的空白。向下取整
        #     # 上下两边留出同样的高度，计算出新的 box: The crop rectangle, as a (left, upper, right, lower)-tuple
        #     box = (0, blank, new_src_width, blank + new_src_height)
        # # 切图
        # new_src_image = src_image.crop(box)

        # 生成目标缩略图
        src_image.thumbnail((dst_width, dst_height))
        return src_image.tobytes()

# =============================== 调试用 ===============================
    def bucket_list_files(self, bucket_name, prefix):
        """
        列出存储桶中所有对象
        :param bucket_name: 同名
        :param prefix: 前缀
        :return:
        """
        try:
            files_list = self.client.list_objects(bucket_name=bucket_name, prefix=prefix, recursive=True)
            for obj in files_list:
                print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
                      obj.etag, obj.size, obj.content_type)
        except S3Error as e:
            print("[error]:", e)

    def bucket_policy(self, bucket_name):
        """
        列出桶存储策略
        :param bucket_name:
        :return:
        """
        try:
            policy = self.client.get_bucket_policy(bucket_name)
        except S3Error as e:
            print("[error]:", e)
            return None
        return policy

    def get_file(self, bucket_name, file, file_path):
        """
        下载保存文件保存本地
        :param bucket_name:
        :param file:
        :param file_path:
        :return:
        """
        self.client.fget_object(bucket_name, file, file_path)


file_minio = FileMinio()

if __name__ == '__main__':
    # file_minio.bucket_list_files('head-pic', prefix=None)
    print(BytesIO(b'123'))
