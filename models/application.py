"""Application DB Models"""
# coding: utf-8
from sqlalchemy import (
    CHAR,CheckConstraint, Column, Integer, Text, text, ForeignKey, Table
)
from sqlalchemy.orm import relationship

from models.common import Base

user_resources = Table(
    'user_resources',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('resource_id', Integer, ForeignKey('resources.id'), primary_key=True)
)

class Users(Base):    # pylint:disable=too-few-public-methods
    """User model"""
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("active in ('Y', 'N')"),
        CheckConstraint("admin in ('Y', 'N')"),
    )

    id = Column(Integer, primary_key=True)
    userid = Column(Text, nullable=False, unique=True)
    passwd = Column(Text, nullable=False, server_default=text("''"))
    surname = Column(Text, nullable=False)
    forename = Column(Text, nullable=False)
    telno = Column(Text, nullable=False)
    addr1 = Column(Text)
    addr2 = Column(Text)
    city = Column(Text)
    state = Column(Text)
    postcode = Column(Text)
    active = Column(CHAR(1), nullable=False, server_default=text("'Y'"))
    admin = Column(CHAR(1), nullable=False, server_default=text("'N'"))

    resources = relationship("Resources", secondary=user_resources, back_populates="users")

class Resources(Base):
    """Resource model defined by developer"""
    __tablename__ = 'resources'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    description = Column(Text)

    users = relationship("Users", secondary=user_resources, back_populates="resources")