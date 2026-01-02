"""Configuration management using Marshmallow for Python 2.7.13"""

import os
import yaml
from pathlib2 import Path
from voluptuous import Schema, Required, Optional, All, Range, Coerce, ALLOW_EXTRA, In
# from voluptuous.util import DefaultTo
from modules.common.utils import initialize_application


DEFAULT_CFG_NAME = "config.yaml"


def enum_validator(enum_class):
    """Create a validator for enum values."""
    def validator(value):
        if isinstance(value, enum_class):
            return value
        # Try to match by value
        for member in enum_class:
            if member.value == value:
                return member
        # Try to match by name
        try:
            return enum_class[value.upper()]
        except (KeyError, AttributeError):
            raise ValueError("Invalid {}: {}. Must be one of: {}".format(
                enum_class.__name__,
                value,
                ', '.join([m.value for m in enum_class])
            ))
    return validator



DATA_STRUCTURE_SCHEMA = Schema({
    Required("dir"): str,
})

DATABASE_STRUCTURE_SCHEMA = Schema({
    Required("name"): str,
    Required("fl_name_template"): str,
    Required("engine_template"): str,
})


LOGGER_CFG_SCHEMA = Schema({
    Optional("level", default="DEBUG"): All(str.upper, In([
        "DEBUG",
        "INFO",
        "WARNING",
        "WARN",
        "ERROR",
        "CRITICAL",
        "EXCEPTION",
    ])),
    Optional("timestamp_format", default="%Y-%m-%d::%H:%M:%S"): str,
    Optional("log_format", default="[{level}] [{timestamp}] {message}"): str,
    Optional("coloring", default=True): bool,
    Optional("use_stdout", default=True): bool,
})

LOGGER_SCHEMA = Schema({
    Required("dir"): str,
    Required("name"): str,
    Optional("config", default={}): LOGGER_CFG_SCHEMA
})


CONFIG_SCHEMA = Schema({
    Optional("debug", default=False): bool,
    Required("db"): DATABASE_STRUCTURE_SCHEMA,
    Required("data"): DATA_STRUCTURE_SCHEMA,
    Required("log"): LOGGER_SCHEMA
})


class YamlSettingsLoader(object):
    """Settings loader that reads configuration data from YAML files."""
    def __init__(self, yml_cfg=DEFAULT_CFG_NAME):
        cfg_path = Path(yml_cfg).resolve()
        if not cfg_path.exists() or not cfg_path.is_file():
            module_dir = initialize_application()
            cfg_path = module_dir.joinpath(yml_cfg)

        if not cfg_path.exists() or not cfg_path.is_file():
            self.cfg_file = None
        else:
            self.cfg_file = cfg_path

    def load(self):
        """Read yaml file and return it as dict of settings."""
        pass
        if self.cfg_file is None:
            data = {}
        elif not (self.cfg_file.exists() and self.cfg_file.is_file()):
            data = {}
        else:
            with open(str(self.cfg_file), "r") as fl:
                data = yaml.safe_load(fl)
        return data


class DataConfig(object):
    """Application configuration"""

    def __init__(self, data, base_dir):
        validated = DATA_STRUCTURE_SCHEMA(data)
        self.dir = validated["dir"]
        self.absolute_dir = base_dir.joinpath(self.dir).resolve()

class DataBaseConfig(object):
    """DataConfig Database configuration"""

    def __init__(self, data, base_dir):
        validated = DATABASE_STRUCTURE_SCHEMA(data)
        self.db_name = validated["fl_name_template"].format(validated["name"])

        self.db_path = base_dir.joinpath(self.db_name)
        self.absolute_db_path = self.db_path.resolve()

        self.uri = validated["engine_template"].format(self.absolute_db_path)

class LoggerSetup(object):
    """Logger instance configuration"""

    def __init__(self, data):
        validated = LOGGER_CFG_SCHEMA(data)
        self.level = validated["level"].strip().upper()
        self.timestamp_format = validated["timestamp_format"]
        self.log_format = validated["log_format"].decode('utf-8')
        self.coloring = validated["coloring"]
        self.use_stdout = validated["use_stdout"]



class LoggerConfig(object):
    """Application Logger Configuration"""

    def __init__(self, data, base_dir):
        validated = LOGGER_SCHEMA(data)
        self.dir = validated["dir"]
        self.absolute_dir = base_dir.joinpath(self.dir)
        self.file = self.absolute_dir.joinpath(
            "{}.log".format(validated["name"])
        )
        self.config = LoggerSetup(data=validated["config"])


class Settings(object):
    """Base Settings object that reads config from different settings sources and merges them."""

    __instance__ = None
    __env_prefix__ = "be_"

    def __new__(cls):
        if cls.__instance__ is None:
            cls.__instance__ = super(Settings, cls).__new__(cls)
        return cls.__instance__

    def __init__(self, cfg_path=DEFAULT_CFG_NAME):
        self.base_folder = Path.cwd().resolve().absolute()
        self._yaml_config = CONFIG_SCHEMA(
            self._load_yaml_config(cfg_path=cfg_path)
        )
        self.debug = self._yaml_config.get('debug', False)
        self.data = DataConfig(self._yaml_config["data"], base_dir=self.base_folder)
        self.db = DataBaseConfig(self._yaml_config["db"], base_dir=self.data.absolute_dir)
        self.logger = LoggerConfig(self._yaml_config["log"], base_dir=self.base_folder)


    def _load_yaml_config(self, cfg_path):
        config_path = Path(cfg_path).resolve().absolute()
        if not (config_path.exists() and config_path.is_file()):
            raise RuntimeError(
                "Config file '{}' does not exists or not a file".format(
                    config_path
                )
            )
        cfg_data =  YamlSettingsLoader(config_path).load()
        self._load_env_overrides(cfg_data) # Override with environment variables
        return cfg_data

    def _load_env_overrides(self, config_data):
        """Load environment variable overrides with 'be_' prefix."""
        for key, value in os.environ.items():
            if key.lower().startswith(self.__env_prefix__):
                # Remove prefix and split by '__' for nested keys
                config_key = key[len(self.__env_prefix__):].lower()
                keys = config_key.split('__')
                # Navigate to the nested dict and set value
                current = config_data
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value

# cfg = Settings()
