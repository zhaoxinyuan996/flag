from functools import wraps
from threading import Lock
from typing import Callable


def lock_wrap(lock: Lock):
    """线程锁"""
    def f1(func: Callable):
        @wraps(func)
        def f2(*args, **kwargs):
            # from threading import get_ident
            # log.error(f'{get_ident()}, {func}, {lock}')
            with lock:
                return func(*args, **kwargs)
        return f2
    return f1
