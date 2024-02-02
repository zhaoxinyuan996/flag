from functools import wraps
from threading import Lock
from typing import Callable


def thread_lock(lock: Lock):
    """线程锁"""
    def f1(func: Callable):
        @wraps(func)
        def f2(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return f2
    return f1
