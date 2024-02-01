import logging
from time import sleep
from util.msg_middleware import MqLocal, QueueType

log = logging.getLogger(__name__)

if __name__ == '__main__':
    MqLocal.monitor()
