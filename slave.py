import logging
import signal
from threading import Thread
from time import sleep
from common.user import flush as user_flush
from common.flag import flag_like
from util.msg_middleware import mq_local, mq_flag_like
from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger(__name__)


def flush_before_exit(signum, frame):
    # 退出前写入
    log.warning('flush_before_exit')
    user_flush()
    flag_like.flush()


# 注册定时刷新任务
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
scheduler = BackgroundScheduler()
scheduler.add_job(flag_like.flush, 'interval', seconds=1)
scheduler.start()

if __name__ == '__main__':

    signal.signal(signal.SIGTERM, flush_before_exit)

    Thread(target=mq_local.loop).start()
    Thread(target=mq_flag_like.loop).start()
    while True:
        sleep(999)
