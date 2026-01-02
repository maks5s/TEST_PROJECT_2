#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Structlog-based logger module with singleton pattern and configurable output.

Features:
    - Singleton logger instances per file (using metaclass)
    - Dual output: stdout + file
    - Configurable log levels and message formats
    - Pretty printing for dict-like objects
    - Colorized output support
    - ConsoleRenderer for local runs
"""
import abc
import io
import os
import pprint
import sys
from datetime import datetime

import better_exceptions
import structlog
from pathlib2 import Path
from six import PY2, StringIO, string_types
from structlog.dev import ConsoleRenderer

try:
    import colorama
except ImportError:
    colorama = None

# Default configuration
DEFAULT_LOG_FORMAT = u'[{level}] [{timestamp}] {message}'
DEFAULT_TIMESTAMP_FORMAT = "%Y-%m-%d::%H:%M:%S"
DEFAULT_LOG_LEVEL = "DEBUG"


class SingletonMeta(type):

    """
    Metaclass for implementing Singleton pattern.
    Ensures only one instance per unique configuration exists.
    """
    _instances = {}
    _lock = None  # Python 2 doesn't need threading.Lock for simple cases

    def __call__(cls, *args, **kwargs):
        """
        Control instance creation.

        Returns:
            object: Singleton instance for given configuration
        """
        # Create unique key based on log_file path
        log_file = kwargs.get('log_file', args[0] if args else 'default.log')
        if not isinstance(log_file, Path):
            log_file = Path(log_file)

        key = str(log_file.absolute())

        if key not in cls._instances:
            instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
            cls._instances[key] = instance

        return cls._instances[key]


class BaseProcessor(object):

    """Abstract base class for log processors."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, logger, method_name, event_dict):
        """
        Process log entry.

        Args:
            logger: Logger instance
            method_name (str): Log method name
            event_dict (dict): Event dictionary

        Returns:
            dict: Processed event dictionary
        """
        pass


class FileWriterProcessor(BaseProcessor):

    """Processor to write logs to a file."""

    def __init__(
        self,
        file_path,
        timestamp_format=DEFAULT_TIMESTAMP_FORMAT,
        log_format=DEFAULT_LOG_FORMAT,
    ):
        """
        Initialize file writer.

        Args:
            file_path (str): Path to log file
            log_format (str): Log message format string
            timestamp_format (str): Timestamp format string
        """
        self.file_path = file_path
        self.log_format = log_format
        self.timestamp_format = timestamp_format
        self._ensure_directory()
        self.file_handle = None

    def _ensure_directory(self):
        """Create directory for log file if it doesn't exist."""
        log_dir = Path(self.file_path).parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

    def __call__(self, logger, method_name, event_dict):
        """
        Process and write log entry to file.

        Args:
            logger: Logger instance
            method_name (str): Log method name
            event_dict (dict): Event dictionary

        Returns:
            dict: Unmodified event dictionary
        """
        if self.file_handle is None:
            self.file_handle = io.open(self.file_path, 'a', encoding='utf-8')
            print("=" * 40)
            print(self.file_path)
            print("=" * 40)

        # Format timestamp
        timestamp = datetime.now().strftime(self.timestamp_format)

        # Format level
        level = method_name.upper()

        # Format message
        event = event_dict.get('event', '')

        # Build log line
        log_line = self.log_format.format(level=level, timestamp=timestamp, message=event)

        # Add extra fields if present
        extra_fields = []
        for key, value in event_dict.items():
            if key not in ['event', 'timestamp', 'level']:
                extra_fields.append(u"\n\t{key}: {value}".format(key=key, value=value))

        if extra_fields:
            log_line += u"".join(extra_fields)

        # Write to file
        try:
            self.file_handle.write(log_line + u"\n")
            self.file_handle.flush()
        except Exception as e:
            sys.stderr.write("Error writing to log file: {}\n".format(e))

        return event_dict

    def __del__(self):
        """Close file handle on cleanup."""
        if self.file_handle:
            try:
                self.file_handle.close()
            except Exception:
                pass


class LevelFilter(BaseProcessor):

    """Filter logs by minimum level."""

    LEVEL_MAP = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "warn": 30,
        "error": 40,
        "critical": 50,
        "exception": 60,
    }

    def __init__(self, min_level):
        """
        Initialize level filter.

        Args:
            min_level (str): Minimum log level (DEBUG, INFO, etc.)
        """
        self.min_level = self._get_level_number(min_level)

    @staticmethod
    def _get_level_number(level_name):
        """
        Convert level name to numeric value.

        Args:
            level_name (str): Level name

        Returns:
            int: Numeric level value
        """
        levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50,
            'EXCEPTION': 50,
        }
        return levels.get(level_name.upper(), 10)

    def __call__(self, logger, method_name, event_dict):
        """
        Filter log by level.

        Args:
            logger: Logger instance
            method_name (str): Log method name
            event_dict (dict): Event dictionary

        Returns:
            dict: Event dictionary or raises DropEvent
        """
        current_level = self.LEVEL_MAP.get(method_name.lower(), 0)
        if current_level < self.min_level:
            raise structlog.DropEvent
        return event_dict


class EnvironmentDetector(object):

    """Detect runtime environment (local vs production)."""

    LOCAL_ENV_INDICATORS = ['local', 'dev', 'development']

    @classmethod
    def is_local_run(cls):
        """
        Detect if running locally.

        Returns:
            bool: True if local run detected
        """
        env = os.environ.get('ENVIRONMENT', '').lower()
        env_short = os.environ.get('ENV', '').lower()
        is_production = os.environ.get('PRODUCTION', False)

        env_checks = [
            env in cls.LOCAL_ENV_INDICATORS,
            env_short in cls.LOCAL_ENV_INDICATORS,
            not is_production,
        ]
        return any(env_checks) or True  # Default to local


class LoggerConfig(object):

    """Configuration class for logger settings."""

    def __init__(
        self,
        log_file='logs.log',
        enable_stdout=True,
        log_level='DEBUG',
        timestamp_format=DEFAULT_TIMESTAMP_FORMAT,
        log_format=DEFAULT_LOG_FORMAT,
        use_colors=True
    ):
        """
        Initialize logger configuration.

        Args:
            log_file (str or Path): Path to log file
            enable_stdout (bool): Enable console output
            log_level (str): Minimum log level
            timestamp_format (str): Timestamp format string
            log_format (str): Log message format string
            use_colors (bool): Enable colorized output
        """
        self.log_file = Path(log_file) if not isinstance(log_file, Path) else log_file
        self.enable_stdout = enable_stdout
        self.log_level = log_level.upper()
        self.timestamp_format = timestamp_format
        self.log_format = log_format
        self.use_colors = use_colors

    def get_log_file_absolute(self):
        """
        Get absolute path to log file.

        Returns:
            str: Absolute path
        """
        return str(self.log_file.absolute())


class CustomConsoleRenderer(ConsoleRenderer):

    @staticmethod
    def _init_colorama_values(force):
        if force:
            colorama.deinit()
            colorama.init(strip=False)
        else:
            colorama.init()

    @staticmethod
    def _pad(s, l):
        """
        Pads *s* to length *l*.
        """
        missing = l - len(s)
        return s + " " * (missing if missing > 0 else 0)

    def __call__(self, _, __, event_dict):
        # Initialize lazily to prevent import side-effects.
        if self._init_colorama:
            self._init_colorama_values(self._force_colors)
            self._init_colorama = False
        sio = StringIO()

        level = event_dict.pop("level", None)
        if level is not None:
            msg = "[{0}{1}{2}]".format(
                self._level_to_color[level],
                self._pad(level, self._longest_level),
                self._styles.reset,
            )
            sio.write(msg)

        ts = event_dict.pop("timestamp", None)
        if ts is not None:
            msg = "[{0}{1}{2}] - ".format(
                self._styles.timestamp,
                str(ts),
                self._styles.reset,
            )
            sio.write(msg)

        # force event to str for compatibility with standard library
        event = event_dict.pop("event")
        if not PY2 or not isinstance(event, string_types):
            event = str(event)

        if event_dict:
            event = self._pad(event,
                              self._pad_event) + self._styles.reset + " "
        else:
            event += self._styles.reset
        sio.write(self._styles.bright + event)

        logger_name = event_dict.pop("logger", None)
        if logger_name is not None:
            sio.write(
                "[{}{}{}{}]".format(
                    self._styles.logger_name,
                    self._styles.bright,
                    logger_name,
                    self._styles.reset
                )
            )

        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)

        def format_evt(styles, key, value):
            return "{}{}{} = {}{}{}".format(
                styles.kv_key,
                key,
                styles.reset,
                styles.kv_value,
                value,
                styles.reset
            )
        msg = "\n\t".join(format_evt(self._styles, key, value) for key, value in event_dict.iteritems())
        sio.write("\n\t" + msg if msg else "")

        if stack is not None:
            sio.write("\n{}".format(stack))
            if exc is not None:
                sio.write("\n\n{}\n".format("=" * 79))
        if exc is not None:
            sio.write("\n{}".format(exc))

        return sio.getvalue()


class StructLogger(object):

    """
    Main logger class with singleton pattern.

    Provides structured logging with file and console output.
    """

    __metaclass__ = SingletonMeta

    def __init__(
        self,
        log_file='logs.log',
        enable_stdout=True,
        log_level='DEBUG',
        timestamp_format=DEFAULT_TIMESTAMP_FORMAT,
        log_format=DEFAULT_LOG_FORMAT,
        use_colors=True
    ):
        """
        Initialize logger instance.

        Args:
            log_file (str or Path): Path to log file
            enable_stdout (bool): Enable console output
            log_level (str): Minimum log level
            timestamp_format (str): Timestamp format string
            log_format (str): Log message format string
            use_colors (bool): Enable colorized output
        """
        self.config = LoggerConfig(
            log_file=log_file,
            enable_stdout=enable_stdout,
            log_level=log_level,
            timestamp_format=timestamp_format,
            log_format=log_format,
            use_colors=use_colors
        )

        self._logger = None
        self._configure()

    def _configure(self):
        """Configure structlog with processors."""
        processors = self._build_processor_chain()

        if self.config.enable_stdout:
            stream_io = sys.stdout
        else:
            stream_io = open(os.devnull, 'w')

        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(stream_io),
            cache_logger_on_first_use=True,
        )

        self._logger = structlog.get_logger(self.config.log_file.stem)

    @staticmethod
    def better_traceback(exc_info):
        """
        Pretty-print *exc_info* to *sio* using the ``better-exceptions`` package.

        To be passed into `ConsoleRenderer`'s ``exception_formatter`` argument.

        Used by default if ``better-exceptions`` is installed and ``rich`` is
        absent.

        .. versionadded:: 21.2
        """
        return "\n" + "".join(better_exceptions.format_exception(*exc_info))

    @staticmethod
    def custom_renderer(logger, name, event_dict):
        return "EVENT={event} PORT={port} REASON={reason}".format(**event_dict)

    @staticmethod
    def custom_timestamper(logger, method_name, event_dict):
        """Add custom timestamp to event_dict"""
        event_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return event_dict

    def _build_processor_chain(self):
        """
        Build processor chain for structlog.

        Returns:
            list: List of processors
        """

        processors = [
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt=self.config.timestamp_format),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(), structlog.processors.format_exc_info,
            LevelFilter(self.config.log_level)
        ]

        # Add file writer
        processors.append(
            FileWriterProcessor(
                self.config.get_log_file_absolute(),
                log_format=self.config.log_format,
                timestamp_format=self.config.timestamp_format
            )
        )

        # Add console renderer if stdout enabled
        if self.config.enable_stdout:
            if EnvironmentDetector.is_local_run():
                processors.append(
                    CustomConsoleRenderer(
                        colors=self.config.use_colors,
                        level_styles={
                            "critical": colorama.Fore.RED,
                            "exception": colorama.Fore.RED,
                            "error": colorama.Fore.LIGHTRED_EX,
                            "warn":colorama.Fore.YELLOW,
                            "warning": colorama.Fore.YELLOW,
                            "info": colorama.Fore.GREEN,
                            "debug": colorama.Fore.BLUE,
                            "notset": colorama.Back.RED,
                        }
                    )
                )
            else:
                processors.append(
                    structlog.processors.KeyValueRenderer(
                        key_order=['timestamp', 'level', 'event'],
                    )
                )
        return processors

    def debug(self, message, **kwargs):
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message, **kwargs):
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message, **kwargs):
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def warn(self, message, **kwargs):
        """Alias for warning."""
        self.warning(message, **kwargs)

    def error(self, message, **kwargs):
        """Log error message."""
        self._logger.error(message, **kwargs)

    def critical(self, message, **kwargs):
        """Log critical message."""
        self._logger.critical(message, **kwargs)

    def exception(self, message, **kwargs):
        """
        Log exception message with traceback.

        Should be called from an exception handler.

        Args:
            message (str): Log message
            **kwargs: Additional context
        """
        message = self.better_traceback(sys.exc_info())
        self._logger.exception(message, **kwargs)

    def pretty_print(self, level, message, data_dict):
        """
        Pretty print a dictionary with a log message.

        Args:
            level (str): Log level (debug, info, warning, error, critical)
            message (str): Log message
            data_dict (dict): Dictionary to pretty print
        """
        formatted_dict = pprint.pformat(data_dict, indent=4, width=80)
        log_method = getattr(self, level.lower())
        log_method(message, formatted_data=u"\n" + formatted_dict)

    def get_logger(self):
        """
        Get underlying structlog logger.

        Returns:
            structlog.BoundLogger: Logger instance
        """
        return self._logger


def get_logger(
    log_file='logs.log',
    enable_stdout=True,
    log_level='DEBUG',
    timestamp_format=DEFAULT_TIMESTAMP_FORMAT,
    log_format=DEFAULT_LOG_FORMAT,
    use_colors=True
):
    """
    Get or create a logger instance (singleton pattern).

    Args:
        log_file (str or Path): Path to log file
        enable_stdout (bool): Enable console output
        log_level (str): Minimum log level
        timestamp_format (str): Timestamp format string
        log_format (str): Log message format string
        use_colors (bool): Enable colorized output

    Returns:
        StructLogger: Logger instance
    """
    return StructLogger(
        log_file=log_file,
        enable_stdout=enable_stdout,
        log_level=log_level,
        timestamp_format=timestamp_format,
        log_format=log_format,
        use_colors=use_colors
    )


# Example usage
if __name__ == '__main__':
    # Create logger
    LOG = get_logger(
        log_file='test.log',
        enable_stdout=True,
        log_level='DEBUG',
        use_colors=True)

    # Test different log levels
    LOG.debug('This is a debug message')
    LOG.info('This is an info message')
    LOG.warning('This is a warning message')
    LOG.error('This is an error message')
    LOG.critical('This is a critical message')

    # Test with extra fields
    LOG.info(
        'Project created or updated',
        name='test',
        type='cot',
        input_source='id',
        cis_source='cis-id',
        timestamp='time'
    )

    # Test pretty print
    test_data = {
        'name': 'test_project',
        'settings': {
            'debug': True,
            'timeout': 30,
            'retries': 3
        },
        'items': ['item1', 'item2', 'item3']
    }
    LOG.pretty_print('info', 'Configuration data:', test_data)

    # Test multiline message
    LOG.info('Try to custom_log\nmultiple string\nlines')

    # Test singleton pattern
    LOG2 = get_logger('test.log')
    print("Singleton test - Same instance: {}".format(LOG is LOG2))

    # Test different file logger
    LOG3 = get_logger('another.log')
    LOG3.info('This goes to another file')
    print("Different file test - Different instance: {}".format(LOG is not LOG3))

    # Test pretty print on instance
    LOG.pretty_print('debug', 'Debug data:', {'key': 'value'})

    # Test exception logging
    print("\n--- Testing exception logging ---")
    try:
        result = 1 / 0
    except ZeroDivisionError:
        LOG.exception('Division by zero occurred', operation='1/0')

    try:
        data = {
            'key': 'value'
        }
        value = data['nonexistent_key']
    except KeyError:
        LOG.exception('Key not found in dictionary', attempted_key='nonexistent_key')

    print("\n--- Exception logging complete ---")
    a = 1
    b = 0
    d = (a + 5) / b
