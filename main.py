import threading

from app import app
from common.job import DelayJob


if __name__ == '__main__':
    threading.Thread(target=DelayJob.run).start()
    app.run()
