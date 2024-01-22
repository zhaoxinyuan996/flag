import threading
from util.config import dev
from app import app
from common.job import DelayJob


if dev:
    threading.Thread(target=DelayJob.run).start()


if __name__ == '__main__':
    if dev:
        print('dev')
        app.run()
