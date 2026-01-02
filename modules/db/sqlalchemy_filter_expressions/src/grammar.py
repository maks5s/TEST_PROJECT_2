"""Contains Lark grammar definition of simple expression language"""

GRAMMAR = """
    ?start: expression

    ?expression: logical_expr

    ?logical_expr: comparison_expr
                | logical_expr "and" logical_expr -> and_op
                | logical_expr "or" logical_expr  -> or_op
                | "not" logical_expr             -> not_op

    ?comparison_expr: field ":" operator ":" value_expr

    field: CNAME
    operator: OPERATOR

    value_expr: single_value                         -> single_value_expr
              | single_value ("," single_value)+     -> list_value_expr

    !single_value: ESCAPED_STRING -> string_value
                 | NUMBER        -> number_value
                 | CNAME         -> name_value

    OPERATOR: "eq"|"neq"|"gt"|"gte"|"lt"|"lte"|"in"|"not_in"|"between"|"like"|"ilike"|"contains"

    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.NUMBER
    %import common.WS

    %ignore WS
"""
