import os
import logging
import time
from util.config import config
from logging.handlers import TimedRotatingFileHandler


def setup_logger(instance: str):
    """初始化日志模块"""
    level = config['log_level']
    default_file = f'{instance}.log'
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    abs_file = os.path.join(log_dir, default_file)
    # 这个日志滚动只能处理常开进程，如果每天重启一次，会重置掉内部flag导致不会滚动
    # 这里手动判断下当前日志的首行日期位，如果不同就重命名，其他情况报错直接忽略
    try:
        with open(os.path.join(log_dir, default_file), 'r', encoding='utf-8') as f:
            date = f.read(10)
        if date and date != time.strftime('%Y-%m-%d'):
            os.rename(
                os.path.join(log_dir, default_file),
                os.path.join(log_dir, default_file + f'.{date}.log')
            )
    except FileNotFoundError:
        open(abs_file, 'w', encoding='utf-8').close()
    except Exception as e:
        print(e)

    logger = logging.getLogger()
    logger.setLevel(level)
    fh = TimedRotatingFileHandler(abs_file, when='D', interval=1, backupCount=30, encoding='utf-8')
    datefmt = '%Y-%m-%d %H:%M:%S'
    format_str = '%(asctime)s %(levelname)s %(message)s '
    formatter = logging.Formatter(format_str, datefmt)
    fh.setFormatter(formatter)
    fh.suffix = '%Y-%m-%d.log'

    # 输出到控制台
    ch = logging.StreamHandler()
    fh.setLevel(level)
    ch.setLevel(level)
    logger.addHandler(fh)
    logger.addHandler(ch)
