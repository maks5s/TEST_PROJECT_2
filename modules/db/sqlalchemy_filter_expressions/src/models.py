"""Data models for AST nodes"""
import typing

import attr

from modules.db.sqlalchemy_filter_expressions import constants as cst

# For Python 2.7 compatibility
FilterNodeType = typing.TypeVar('FilterNodeType', bound='FilterNode')
T = typing.TypeVar('T')


@attr.s(auto_attribs=False)    # auto_attribs is not supported in older versions
class FilterNode(object):
    pass


@attr.s(auto_attribs=False)
class Comparison_Node(FilterNode):
    field = attr.ib(type=str)
    operator = attr.ib(type=cst.ComparisonOp)
    value = attr.ib(type="typing.Any")


@attr.s(auto_attribs=False)
class Collection_Node(FilterNode):
    field = attr.ib(type=str)
    operator = attr.ib(type=cst.CollectionOp)
    values = attr.ib(type="typing.List[typing.Any]")


@attr.s(auto_attribs=False)
class Range_Node(FilterNode):
    field = attr.ib(type=str)
    start = attr.ib(type=typing.Any)
    end = attr.ib(type=typing.Any)


@attr.s(auto_attribs=False)
class Text_Search_Node(FilterNode):
    field = attr.ib(type=str)
    operator = attr.ib(type=cst.TextOp)
    pattern = attr.ib(type=str)


@attr.s(auto_attribs=False)
class Logical_Node(FilterNode):
    operator = attr.ib(type=cst.LogicalOp)
    operands = attr.ib(factory=list, type=typing.List[FilterNode])
