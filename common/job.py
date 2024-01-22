import logging
from multiprocessing import Queue


log = logging.getLogger(__name__)


class DelayJob:
    job_queue = Queue()

    @staticmethod
    def run(q: Queue):
        print(0)
        while True:
            print(111)
            func = q.get()
            print(222)
            log.info(f'run delay job: {func}')
            try:
                func()
            except Exception as e:
                log.error(f'delay job error: {func}')
                log.exception(e)
