from sqlalchemy import Column, Integer, DateTime, String, Boolean, Date, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


"""
This ORM scheme is only operational, don't use it to create the same in database.
"""

Base = declarative_base()


class Organisation(Base):
    __tablename__ = 'organisation'
    id = Column(Integer, Sequence('Organisation_id_seq'), primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Decision(Base):
    __tablename__ = 'decision'
    id = Column(Integer, Sequence('decision_id_seq'), primary_key=True)
    decision_code = Column(String, nullable=False, unique=True)
    decision_date = Column(Date, nullable=False)
    org_id = Column(Integer, ForeignKey('organisation.id'))


class BlockType(Base):
    __tablename__ = 'blocktype'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Entitytype(Base):
    __tablename__ = 'entitytype'
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False, unique=True)


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, Sequence('resource_id_seq'), primary_key=True)
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False)
    last_change = Column(DateTime)
    entitytype_id = Column(Integer, ForeignKey('entitytype.id'), nullable=False)
    value = Column(String, nullable=False)  # May be not unique
    is_custom = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean)


class Content(Base):
    __tablename__ = 'content'
    id = Column(Integer, Sequence('content_id_seq'), primary_key=True)
    outer_id = Column(Integer, nullable=False, unique=True)
    include_time = Column(DateTime)
    hash = Column(String(32))
    last_change = Column(DateTime)
    in_dump = Column(Boolean)
    decision_id = Column(Integer, ForeignKey('decision.id'), nullable=False)
    blocktype_id = Column(Integer, ForeignKey('blocktype.id'), nullable=False)
    entrytype_id = Column(Integer, nullable=False) # ForeignKey('entrytype.id') - not mandatory
    first_dump_id = Column(Integer, ForeignKey('dumpinfo.id'), nullable=False)
    last_dump_id = Column(Integer, ForeignKey('dumpinfo.id'), nullable=False)


class DumpInfo(Base):
    __tablename__ = 'dumpinfo'
    id = Column(Integer, Sequence('dumpinfo_id_seq'), primary_key=True)
    update_time = Column(DateTime, nullable=False)
    update_time_urgently = Column(DateTime)
    parse_time = Column(DateTime, nullable=False)
    parsed = Column(Boolean, default=False)
