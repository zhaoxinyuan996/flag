import logging
from time import sleep
from typing import Callable
from uuid import UUID
import pika
from util import config


log = logging.getLogger(__name__)


class QueueType:
    local_by_ip: str = 'local_by_ip'
    flag_statistics: str = 'flag_statistics'


class MqBase:
    queue_name: ''

    def __init__(self):
        try:
            self.cb = None
            # 创建连接和通道
            user_info = pika.PlainCredentials(**config.mq_auth)  # 用户名和密码
            self.channel = pika.BlockingConnection(pika.ConnectionParameters(
                credentials=user_info, **config.mq_conn)).channel()
            # 声明队列
            self.channel.queue_declare(queue=self.queue_name)
        except Exception as e:
            log.exception(e)

    def register_cb(self, func: Callable):
        self.cb = func

    def put(self, body: str):
        """通过ip获取为详细位置"""
        log.info(f'put {self.queue_name} mq: {body}')
        try:
            self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=body)
        except Exception as e:
            log.error(e)
            self.__init__()
            self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=body)

    def loop(self):
        self.channel.basic_consume(self.queue_name, self.callback, auto_ack=True)
        while True:
            try:
                self.channel.start_consuming()
            except Exception as e:
                log.error(e)
                self.__init__()
            finally:
                log.warning('loopppppppppppppppp')
                sleep(1)

    @staticmethod
    def callback(ch, method, properties, body: bytes):
        raise NotImplementedError


class MqLocal(MqBase):
    queue_name = QueueType.local_by_ip

    def callback(self, ch, method, properties, body: bytes):
        log.info(f'{self.queue_name} callback: {body}')
        user_id, host = body.decode().split('|')
        self.cb(UUID(user_id), host)


class MqFlagStatistics(MqBase):
    queue_name = QueueType.flag_statistics

    def callback(self, ch, method, properties, body: bytes):
        log.info(f'{self.queue_name} callback: {body}')
        user_id, flag_id, key, num = body.decode().split('|')
        user_id = UUID(user_id)
        flag_id = UUID(flag_id)
        num = int(num)
        self.cb(user_id, flag_id, key, num)


mq_local = MqLocal()
mq_flag_statistics = MqFlagStatistics()
