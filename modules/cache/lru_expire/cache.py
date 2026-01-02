"""LRU Cache"""
from datetime import datetime, timedelta
from functools import wraps
from repoze.lru import lru_cache


def lru_cache_expiring(maxsize=128, expires=20):
    """LRU cache decorator"""
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=expires)
        func.expiration = datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.utcnow() >= func.expiration:
                func.clear()
                func.expiration = datetime.utcnow() + func.lifetime
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache
