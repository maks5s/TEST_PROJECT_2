"""Module contains database connection related components."""

import abc
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from pathlib2 import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from modules.common import patterns as pt
from modules.db.sqlalchemy_engine.errors import (
    DbConnectionError, MissingSessionError, SessionMakerNotInitializedError
)


def _get_logger(logger_path):
    basedir = logger_path.parent
    if not basedir.exists():
        basedir.mkdir()
    return get_logger(str(logger_path), level=logging.INFO)


class DatabaseSingleton(object):
    __metaclass__ = pt.ParameterizedSingletonMeta

    def __init__(self, db_path):
        self.db_path = db_path

    @abc.abstractmethod
    def get_transaction(self):
        pass

    @abc.abstractmethod
    def dispose(self, close=True):
        pass


class Database(DatabaseSingleton):
    """Database singleton."""

    __check_same_thread__ = True
    __timeout__ = 15
    __detect_types__ = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES

    __connection_str_tmp__ = 'sqlite:///{}'

    __logs_path__ = Path.cwd().joinpath("logs")
    __logger_base_name__ = Path(__file__).stem

    def __init__(
        self,
        db_path,
        engine_args=None,
        session_maker_args=None,
        custom_engine=None,
    # on_do_connect_event=None,
    ):
        """Database singleton."""
        super(Database, self).__init__(db_path)
        self.db_path = Path(db_path).resolve()

        self.__logger = _get_logger(
            self.__logs_path__.joinpath(
                "{}_{}.log".format(self.__logger_base_name__,
                                   datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))
            )
        )

        engine_args = engine_args or {}

        connect_args = engine_args.get('connect_args', {})
        engine_args['connect_args'] = connect_args
        engine_args['connect_args']['check_same_thread'] = connect_args.get(
            'check_same_thread', self.__check_same_thread__
        )

        session_maker_args = session_maker_args or {}

        if custom_engine:
            self._engine = custom_engine
        else:
            if not (self.db_path.exists() and self.db_path.is_file()):
                raise DbConnectionError(
                    "Cannot connect to the db '{}' because it does not exists or "
                    "not a file".format(db_path)
                )

            db_connection_str = self.__connection_str_tmp__.format(db_path)
            self._engine = create_engine(db_connection_str, **engine_args)

        self._session_maker = sessionmaker(
            bind=self._engine, class_=Session, expire_on_commit=False, **session_maker_args
        )

    @property
    def engine(self):
        """Return an `Engine` object."""
        return self._engine

    @property
    def session_maker(self):
        """Return an `sessionmaker` object."""
        return self._session_maker

    @contextmanager
    def get_transaction(self):
        """
        Return a context manager.

        When entered will deliver an `Connection` with an `Transaction` established.
        """
        with self.engine.begin() as connection:
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise

    def dispose(self, close=True):
        """Dispose of the connection pool."""
        self.engine.dispose(close=close)

    def __del__(self):
        """Dispose of the connection pool."""
        try:
            self.dispose(close=False)
        except Exception as err:
            self.__logger.warning("Dispose of the connection pool failed: {}.".format(err))

class DatabaseSession:
    """Database Session."""

    def __init__(self, db_path, session_args=None, commit_on_exit=False, session_maker=None):
        """Database session."""
        self.token = None

        self.session_args = session_args or {}
        self.commit_on_exit = commit_on_exit
        if session_maker is None:
            db = Database(db_path)
            self._session_maker = db.session_maker
        else:
            self._session_maker = session_maker
        self._session = None

    @property
    def session(self):
        """Return an instance of Session local to the current async context."""
        if self._session is None:
            raise MissingSessionError

        return self._session

    def __enter__(self):
        """Database session context enter."""
        if not isinstance(self._session_maker, sessionmaker):
            raise SessionMakerNotInitializedError

        self._session = self._session_maker(**self.session_args)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """Database session context exit."""
        try:
            if exc_type is not None:
                self.session.rollback()
            elif self.commit_on_exit:
                self.session.commit()
        finally:
            self.session.close()
