import logging
import platform
from multiprocessing import Queue

log = logging.getLogger(__name__)


def delay_shell(q: Queue):
    while True:
        func = q.get()
        log.info(f'run delay job: {func}')
        try:
            func()
        except Exception as e:
            log.error(f'delay job error: {func}')
            log.exception(e)


class DelayJob:
    job_queue = Queue()

    if platform.system().lower() == 'windows':
        @classmethod
        def run(cls):
            delay_shell(cls.job_queue)

    else:
        import uwsgidecorators

        @classmethod
        @uwsgidecorators.thread
        def run(cls):
            delay_shell(cls.job_queue)
