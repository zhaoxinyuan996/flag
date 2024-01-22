import threading
from util.log import setup_logger

setup_logger()


if __name__ == '__main__':
    from app import app
    from common.job import DelayJob
    from util.config import dev, config

    if not dev:
        threading.Thread(target=DelayJob.run).start()
    if dev:
        print('dev')
        app.run()
    else:
        app.run(host=config['web']['ip'], port=config['web']['port'])
