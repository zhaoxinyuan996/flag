import logging
from time import sleep
from util.msg_middleware import MqLocal, QueueType

log = logging.getLogger(__name__)

if __name__ == '__main__':
    while True:
        try:
            MqLocal(QueueType.local_by_ip).get()
        except Exception as e:
            log.error(e)
        finally:
            sleep(5)
