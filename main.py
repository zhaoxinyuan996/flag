import multiprocessing
import platform

from util.config import dev
from app import app
from common.job import DelayJob


if not dev:
    multiprocessing.Process(target=DelayJob.run, args=(DelayJob.job_queue, )).start()


if __name__ == '__main__':
    if dev:
        print('dev')
        app.run()
