"""Common Scriptpartner database"""
from sqlalchemy import Column, Float, Index, Integer, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

DECLARATIVE_BASE = declarative_base()


class Base(DECLARATIVE_BASE):    # pylint:disable=too-few-public-methods
    """Base model class"""
    __abstract__ = True

    def to_dict(self, flat=False, exclude_keys=None):    # pylint:disable=unused-argument
        """Convert a data type (like a Pydantic model) to something compatible with JSON

            Inspired by  https://fastapi.tiangolo.com/tutorial/encoder/
        """
        exclude_keys = exclude_keys or []
        col_attrs = inspect(self).mapper.mapper.column_attrs

        raw_dict = {}
        for col in col_attrs:
            if col.key not in exclude_keys:
                raw_dict[col.key] = getattr(self, col.key)

        return raw_dict