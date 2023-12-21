import threading

from app import app
from common.job import DelayJob
from util.config import dev

if __name__ == '__main__':
    if dev:
        print('dev')
        app.run()
    else:
        threading.Thread(target=DelayJob.run).start()
        app.run(host='0.0.0.0', port=80)

