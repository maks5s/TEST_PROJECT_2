"""Contains Databases Connections"""
from pathlib2 import Path

from modules.db.sqlalchemy_engine import DatabaseSession


def get_db_session(db_path, commit_on_exit=False):
    """Get connection to the given database"""
    if not isinstance(db_path, Path):
        db_path = Path(db_path)
    db_path = db_path.resolve()

    if not (db_path.exists() and db_path.is_file()):
        raise RuntimeError("The database object '{}' does not exists or not a file".format(db_path))
    return DatabaseSession(db_path, commit_on_exit=commit_on_exit)


