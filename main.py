import sys
from modules.common import utils as ut
from modules.config import Settings
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models.application import Users
from models.common import DECLARATIVE_BASE
from modules.cache import lru_expire as lrue

import random
from pathlib2 import Path
from modules.logger import get_logger
from tests.fixtures import UserFactory

from queries.application import get_active_users, get_inactive_users, get_admin_users
from modules.elapsed_time import elapsed_timer


class TestApp(object):
    """Main Logic implementation"""

    def __init__(self):
        self._config = None
        self._db_engine = None
        self._session_factory = None

        self._logger = None
        self._configured = False

    def _load_config(self, force=False):
        if self._config is None or force:
            self._config = Settings()

    def _create_engine(self):
        if self._config is None:
            raise RuntimeError(
                "Call load config before"
            )
        if self._db_engine is None:
            self._db_engine = create_engine(
                self._config.db.uri,
                echo=True
            )
            self._logger.debug("Created Database Engine")

    def _log_sql(self, conn, cursor, statement, parameters, context, executemany):
        self._logger.info(
            "sql_query",
            statement=statement,
            parameters=parameters,
            executemany=executemany
        )

    def _log_sql_complete(self, conn, cursor, statement, parameters, context, executemany):
        self._logger.info(
            "sql_query_complete",
            statement=statement
        )

    def _register_listeners(self):
        if self._db_engine is None:
            raise RuntimeError(
                "Call create_engine before"
            )
        event.listen(self._db_engine, "before_cursor_execute", self._log_sql)
        event.listen(self._db_engine, "after_cursor_execute", self._log_sql_complete)


    def _init_db(self):
        if self._db_engine is None:
            self._logger.error(
                "Cannot initialize database. Call create_engine before"
            )
        else:
            DECLARATIVE_BASE.metadata.create_all(self.engine)


    @property
    def engine(self):
        self._create_engine()
        return self._db_engine

    def _create_db_session_factory(self):
        if self._db_engine is None:
            raise RuntimeError(
                "Call create_engine before"
            )
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine)
            self._logger.debug("Created Database Session Factory")

    def _create_logger(self):
        if self._config is None:
            raise RuntimeError(
                "Call load config before"
            )

        if self._logger is None:
            self._logger = get_logger(
                log_file=self._config.logger.file,
                enable_stdout=self._config.logger.config.use_stdout,
                log_level=self._config.logger.config.level,
                timestamp_format=self._config.logger.config.timestamp_format,
                log_format=self._config.logger.config.log_format,
                use_colors=self._config.logger.config.coloring,
            )

    def setup(self):
        """Used to perform setup tasks"""
        ut.initialize_application()
        self._load_config()
        self._create_logger()
        self._create_engine()
        self._register_listeners()
        self._create_db_session_factory()
        self._init_db()
        self._configured = True


    def alembic_setup(self):
        """Used to perform setup tasks with Alembic"""
        ut.initialize_application()
        self._load_config()
        self._create_logger()
        self._create_engine()
        self._register_listeners()
        self._create_db_session_factory()
        # self._init_db()  # Create tables using migrations
        self._configured = True


    def delete_database(self):
        if not self._configured:
            raise RuntimeError(
                "Can not delete a database file. Call setup first"
            )
        db_fl = Path(self._config.db.absolute_db_path)
        try:
            db_fl.unlink()
            self._logger.debug(
                "Database '{}' deleted successfully".format(db_fl)
            )
        except FileNotFoundError:
            self._logger.error(
                "The database file '{}' does not exist.".format(db_fl)
            )
        except PermissionError:
            self._logger.error(
                "Permission denied to delete the database '{}'.".format(db_fl)
            )

    def teardown(self):
        self.delete_database()

    def populate_users_in_db(self, count=10000, batch_size = 1000):
        """Fill-in users data in application db """
        if not self._configured:
            raise RuntimeError(
                "Application Setup must be called before"
            )

        if batch_size > count:
            batch_size = count

        with self._session_factory() as session:
            user_count = session.query(Users).count()
            if user_count > 0:
                self._logger.warning(
                    "User table is not empty. Skip initialization"
                )
                return
            self._logger.info(
                "User populating: Generate {} users".format(count)
            )

            for i in range(0, count, batch_size):
                users = [UserFactory.build() for _ in range(min(batch_size, count - i))]
                session.bulk_save_objects(users)
                session.commit()
                self._logger.debug(
                    "User populating: Inserted {} users...".format(count)
                )
            self._logger.info("Successfully created {} users!".format(count))


    def get_users(self, execution_count=1000):
        self._logger.info("=" * 40)
        self._logger.info("Retrieving active user '' times".format(execution_count))
        with elapsed_timer() as elapsed:
            for _ in range(execution_count):
                active_usrs = get_active_users(self._session_factory)
                admin_usrs = get_admin_users(self._session_factory)
                inactive_usrs = get_inactive_users(self._session_factory)
            self._logger.info(
                "Retrieved users '{}' times".format(execution_count),
                execution_time = elapsed()
            )

        return {
            "inactive_users": inactive_usrs,
            "active_users": active_usrs,
            "admin_users": admin_usrs,
        }

    @property
    def session_factory(self):
        return self._session_factory


def main():
    logger = get_logger(
        log_file=Path('./logs').joinpath("application").resolve(),
        enable_stdout=True,
        log_level="DEBUG",
        use_colors=True,
    )

    app = TestApp()
    try:
        app.setup()
        app.populate_users_in_db(batch_size=100)
        app.get_users(execution_count=100)
    except RuntimeError as err:
        logger.exception(
            "Can not run application due to the error '{}'".format(err)
        )
        return 1
    else:
        return 0
    finally:
        app.teardown()


if __name__ == "__main__":
    sys.exit(main())
