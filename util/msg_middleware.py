import logging
from time import sleep
from uuid import UUID
import pika
from util import config
from common.user import refresh_user_mq


log = logging.getLogger(__name__)


class QueueType:
    local_by_ip: str = 'local_by_ip'


class MqBase:
    def __init__(self, queue_name: str):
        self.queue_name = queue_name
        # 创建连接和通道
        user_info = pika.PlainCredentials(**config.mq_auth)  # 用户名和密码
        self.channel = pika.BlockingConnection(pika.ConnectionParameters(
            credentials=user_info, **config.mq_conn)).channel()
        # 声明队列
        self.channel.queue_declare(queue=queue_name)

    def put(self, body: str):
        """通过ip获取为详细位置"""
        log.info(f'put_local_by_ip: {body}')
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=body)

    def loop(self):
        self.channel.basic_consume(self.queue_name, self.callback, auto_ack=True)
        self.channel.start_consuming()

    @classmethod
    def monitor(cls: 'MqBase', *args):
        while True:
            try:
                cls.__new__(*args).loop()
            except Exception as e:
                log.error(e)
            finally:
                sleep(5)

    @staticmethod
    def callback(ch, method, properties, body: bytes):
        raise NotImplementedError


class MqLocal(MqBase):
    @staticmethod
    def callback(ch, method, properties, body: bytes):
        user_id, host = body.decode().split('|')
        log.info(f'local_by_ip callback: {body}')
        refresh_user_mq(UUID(user_id), host)

class MqFlagStatistics(MqBase):

    @staticmethod
    def callback(ch, method, properties, body: bytes):




mq_local = MqLocal(QueueType.local_by_ip)
