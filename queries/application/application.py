"""Contains logic to retrieve users info"""
from lark.exceptions import UnexpectedToken

from models.application import Users
from modules.db import sqlalchemy_filter_expressions as sql_fe


def parse_filters(filters_str):
    if isinstance(filters_str, str) and filters_str:
        parser = sql_fe.parser.FilterParser()
        try:
            ast = parser.parse(filters_str)
        except UnexpectedToken:
            ast = None
    else:
        ast = None
    return ast


_FILTER_PARSER = sql_fe.parser.FilterParser()
_AST_CACHE = {}

def optimized_parse_filters(filters_str):
    if not (isinstance(filters_str, str) and filters_str):
        return None

    if filters_str in _AST_CACHE:
        return _AST_CACHE[filters_str]

    try:
        ast = _FILTER_PARSER.parse(filters_str)
        _AST_CACHE[filters_str] = ast
        return ast
    except UnexpectedToken:
        return None


def get_users(session_factory, filter_str=None, to_dict=False):
    """Returns all users matching the given conditions"""
    filter_ast = optimized_parse_filters(filters_str=filter_str)

    with session_factory() as session:
        query = session.query(Users)
        if filter_ast:
            fb = sql_fe.filters.SQLAlchemyFilterBuilder()
            filters = fb.build_filter(filter_ast, Users)
            query = query.filter(filters)
        res = query.all()

    return list(map(lambda x: x.to_dict(), res)) if to_dict else res


def get_inactive_users(session_factory, to_dict=False):
    """Get list of inactive users"""
    return get_users(session_factory, filter_str="active:eq:N", to_dict=to_dict)


def get_active_users(session_factory, to_dict=False):
    """Get list of active categories"""
    return get_users(session_factory, filter_str="active:eq:Y", to_dict=to_dict)


def get_admin_users(session_factory, to_dict=False):
    """Get list of active categories"""
    return get_users(session_factory, filter_str="active:eq:Y and admin:eq:Y", to_dict=to_dict)


def get_users_paginated(session_factory, filter_str=None, to_dict=True, page=1, per_page=10):
    """Returns all users matching the given conditions with pagination"""
    filter_ast = parse_filters(filters_str=filter_str)

    with session_factory() as session:
        query = session.query(Users)

        if filter_ast:
            fb = sql_fe.filters.SQLAlchemyFilterBuilder()
            filters = fb.build_filter(filter_ast, Users)
            query = query.filter(filters)

        total_count = query.count()

        offset = (page - 1) * per_page

        res = query.limit(per_page).offset(offset).all()

    data = [x.to_dict() for x in res] if to_dict else res

    return data, total_count

def get_active_users_paginated(session_factory, to_dict=False, page=1, per_page=10):
    """Get list of active users with pagination"""
    return get_users_paginated(
        session_factory,
        filter_str="active:eq:Y",
        to_dict=to_dict,
        page=page,
        per_page=per_page
    )