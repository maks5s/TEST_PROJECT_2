"""Lark transformer for AST construction"""
from lark import Transformer

from modules.db.sqlalchemy_filter_expressions import constants as cst
from modules.db.sqlalchemy_filter_expressions import models as md


class FilterTransformer(Transformer):

    def and_op(self, args):
        return md.Logical_Node(operator=cst.LogicalOp.AND, operands=list(args))

    def or_op(self, args):
        return md.Logical_Node(operator=cst.LogicalOp.OR, operands=list(args))

    def not_op(self, args):
        return md.Logical_Node(operator=cst.LogicalOp.NOT, operands=list(args))

    def field(self, args):
        return str(args[0])

    def operator(self, args):
        return str(args[0])

    def string_value(self, args):
        value = args[0]
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        return value

    def number_value(self, args):
        return float(args[0])

    def name_value(self, args):
        return str(args[0])

    def single_value_expr(self, args):
        return args[0]

    def list_value_expr(self, args):
        return list(args)

    def comparison_expr(self, args):
        field, op, value = args
        op = str(op)    # Ensure operator is string

        if op in cst.ComparisonOp.values():
            return md.Comparison_Node(field=field, operator=cst.ComparisonOp(op), value=value)
        if op in cst.CollectionOp.values():
            if not isinstance(value, list):
                value = [value]
            return md.Collection_Node(field=field, operator=cst.CollectionOp(op), values=value)
        if op == cst.RangeOp.values():
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("Between operator requires exactly two values")
            return md.Range_Node(field=field, start=value[0], end=value[1])
        if op in cst.TextOp.values():
            return md.Text_Search_Node(field=field, operator=cst.TextOp(op), pattern=str(value))
        raise ValueError("Unknown operator: {}".format(op))
