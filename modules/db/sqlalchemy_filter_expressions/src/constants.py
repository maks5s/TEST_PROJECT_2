"""Query Operator constants and enums"""
from enum import Enum


class BaseEnum(Enum):

    @classmethod
    def members(cls):
        """Returns a dictionary of enum names and their values, avoiding direct __members__ call."""
        return {name: member.value for name, member in cls.__dict__.items() if isinstance(member, cls)}

    @classmethod
    def values(cls):
        return tuple(member.value for _, member in cls.__dict__.items() if isinstance(member, cls))

    @classmethod
    def from_string(cls, name):
        """Get the enum value from its string name."""
        members = cls.members()
        if name in members:
            return members[name]
        raise ValueError("Invalid Status name: {}".format(name))

    @classmethod
    def from_value(cls, value):
        """Get the enum name from its value."""
        for name, val in cls.members().items():
            if val == value:
                return name
        raise ValueError("Invalid Status value: {}".format(value))


class ComparisonOp(BaseEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class CollectionOp(BaseEnum):
    IN = "in"
    NOT_IN = "not_in"


class RangeOp(BaseEnum):
    BETWEEN = "between"


class TextOp(BaseEnum):
    LIKE = "like"
    ILIKE = "ilike"
    CONTAINS = "contains"


class LogicalOp(BaseEnum):
    AND = "and"
    OR = "or"
    NOT = "not"
