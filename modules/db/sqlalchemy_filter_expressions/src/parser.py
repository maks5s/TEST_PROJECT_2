"""Query Filter String Parser"""
from lark import Lark

from modules.db.sqlalchemy_filter_expressions import grammar as gr
from modules.db.sqlalchemy_filter_expressions import models as md
from modules.db.sqlalchemy_filter_expressions import transformers as trns

class FilterParser(object):

    def __init__(self):
        self.parser = Lark(gr.GRAMMAR, parser='lalr', transformer=trns.FilterTransformer())


    def parse(self, expression):
        return self.parser.parse(expression)
