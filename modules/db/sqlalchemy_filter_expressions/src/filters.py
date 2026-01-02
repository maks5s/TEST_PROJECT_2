from sqlalchemy import and_, not_, or_

from modules.db.sqlalchemy_filter_expressions import constants as cst


class SQLAlchemyFilterBuilder(object):

    def build_filter(self, node, model):
        method = getattr(self, 'visit_{}'.format(node.__class__.__name__.strip().lower()), None)
        if method is None:
            raise ValueError("Unsupported node type: {}".format(node.__class__.__name__))
        return method(node, model)

    def visit_comparison_node(self, node, model):
        column = getattr(model, node.field)
        if node.operator == cst.ComparisonOp.EQ:
            return column == node.value
        if node.operator == cst.ComparisonOp.NEQ:
            return column != node.value
        if node.operator == cst.ComparisonOp.GT:
            return column > node.value
        if node.operator == cst.ComparisonOp.GTE:
            return column >= node.value
        if node.operator == cst.ComparisonOp.LT:
            return column < node.value
        if node.operator == cst.ComparisonOp.LTE:
            return column <= node.value

    def visit_collection_node(self, node, model):
        column = getattr(model, node.field)
        if node.operator == cst.CollectionOp.IN:
            return column.in_(node.values)
        if node.operator == cst.CollectionOp.NOT_IN:
            return ~column.in_(node.values)

    def visit_range_node(self, node, model):
        column = getattr(model, node.field)
        return column.between(node.start, node.end)

    def visit_text_search_node(self, node, model):
        column = getattr(model, node.field)
        if node.operator == cst.TextOp.LIKE:
            return column.like(node.pattern)
        if node.operator == cst.TextOp.ILIKE:
            return column.ilike(node.pattern)
        if node.operator == cst.TextOp.CONTAINS:
            return column.contains(node.pattern)

    def visit_logical_node(self, node, model):
        conditions = [self.build_filter(operand, model) for operand in node.operands]
        if node.operator == cst.LogicalOp.AND:
            return and_(*conditions)
        elif node.operator == cst.LogicalOp.OR:
            return or_(*conditions)
        elif node.operator == cst.LogicalOp.NOT:
            return not_(*conditions)
