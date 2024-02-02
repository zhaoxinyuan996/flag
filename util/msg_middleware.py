r"""
本文件的id类型声明为uuid，但是实际是str类型
"""
import logging
import pickle
from functools import wraps
from time import sleep
from typing import Callable
import pika
from util import config


log = logging.getLogger(__name__)


class QueueType:
    local_by_ip: str = 'local_by_ip'
    flag_statistics: str = 'flag_statistics'
    user_message: str = 'user_message'


def cb_log(func):
    @wraps(func)
    def f(self: 'MqBase', ch, method, properties, body: bytes):
        log.info(f'{self.queue_name} callback: {body}')
        return func(self, ch, method, properties, body)
    return f


class MqBase:
    queue_name: ''
    cb: Callable

    def __init__(self):
        try:
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
            log.error(f'put {self.queue_name}: {e}')
            self.__init__()
            self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=body)

    def loop(self):
        self.channel.basic_consume(self.queue_name, self.callback, auto_ack=True)
        while True:
            try:
                self.channel.start_consuming()
            except Exception as e:
                log.error(f'loop {self.queue_name}: {e}')
                self.__init__()
            finally:
                sleep(1)

    @staticmethod
    def callback(ch, method, properties, body: bytes):
        raise NotImplementedError


class MqLocal(MqBase):
    queue_name = QueueType.local_by_ip

    @cb_log
    def callback(self, ch, method, properties, body: bytes):
        user_id, host = body.decode().split('|')
        self.cb(user_id, host)


class MqFlagLike(MqBase):
    queue_name = QueueType.flag_statistics

    @cb_log
    def callback(self, ch, method, properties, body: bytes):
        user_id, flag_id, key, num = body.decode().split('|')
        num = int(num)
        self.cb(user_id, flag_id, key, num)


class MqUserMessage(MqBase):
    queue_name = QueueType.user_message

    @cb_log
    def callback(self, ch, method, properties, body: bytes):
        self.cb(pickle.loads(body))


mq_local = MqLocal()
mq_flag_like = MqFlagLike()
mq_user_msg = MqUserMessage()
