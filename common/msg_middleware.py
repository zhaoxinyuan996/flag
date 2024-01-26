import logging
from uuid import UUID
import pika
from util import config


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


class MqLocal(MqBase):
    def put(self, user_id: UUID, ip: str):
        """通过ip获取为详细位置"""
        body = f'{user_id}|{ip}'
        log.info(f'put_local_by_ip: {body}')
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=body)


mq_local = MqLocal(QueueType.local_by_ip)
