import logging
from queue import Queue


log = logging.getLogger(__name__)


class DelayJob:
    job_queue = Queue()

    @classmethod
    def run(cls):
        while True:
            func = cls.job_queue.get()
            log.info(f'run delay job: {func}')
            try:
                func()
            except Exception as e:
                log.error(f'delay job error: {func}')
                log.exception(e)
