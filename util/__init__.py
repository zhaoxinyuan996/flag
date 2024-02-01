import sys
from .database import db
from .log import setup_logger
print(sys.argv[-1])
setup_logger('slave.log' if sys.argv[-1].endswith('slave.py') else 'flag.log')
