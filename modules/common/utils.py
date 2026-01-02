"""Contains common util functions"""
import inspect
from pathlib2 import Path
import sys
from modules.cache import lru_expire as lrue

def get_module_dir(level= 1):
    """
    Return the absolute directory path of the module that called this function.

    :param level: How far up the call stack to look.
                  1 = direct caller (default)
                  2 = caller of caller, etc.
    """
    # Get the frame of the caller
    frame = inspect.stack()[level]
    module = inspect.getmodule(frame[0])

    if module is None or not hasattr(module, "__file__"):
        filename = frame.filename
    else:
        filename = module.__file__

    return Path(filename).resolve().parent

@lrue.lru_cache_expiring(maxsize=128, expires=200)
def initialize_application():
    """Return absolute path object representing the current directory."""

    cwd_path = Path.cwd().resolve()

    cwd_str = str(cwd_path)

    if cwd_str not in sys.path:
        sys.path.insert(0, cwd_str)
    return cwd_path

