"""Module contains common patterns."""

import abc
import threading


class SingletonABCMeta(abc.ABCMeta):
    """Singletone object"""
    _instances = {}
    _lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(SingletonABCMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ParameterizedSingletonMeta(abc.ABCMeta):
    """Parametrized Singletone object"""
    _instances = {}
    _lock = threading.RLock()

    def __call__(cls, db_path, *args, **kwargs):
        with cls._lock:
            # Use path as the key for different instances
            if (cls, db_path) not in cls._instances:
                cls._instances[(cls, db_path)] = super(ParameterizedSingletonMeta,
                                                       cls).__call__(db_path, *args, **kwargs)
        return cls._instances[(cls, db_path)]
