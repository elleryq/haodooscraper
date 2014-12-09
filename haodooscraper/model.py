# -*- coding: utf-8 -*-

import os
from sqlalchemy import (create_engine,
                        Table, Column, Integer, String, MetaData, ForeignKey,
                        or_)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import func
from flask.ext.jsontools import JsonSerializableBase
from haodooscraper.pagination import Pagination


db_url = os.environ.get("OPENSHIFT_MYSQL_DB_URL", "")

if not db_url:
    raise Exception("Need to set 'OPENSHIFT_MYSQL_DB_URL'.")

db_url = db_url.replace("mysql://", "mysql+pymysql://")
db_url = db_url + "haodooscraper?charset=utf8"
engine = create_engine(db_url)
Base = declarative_base(cls=(JsonSerializableBase,))
Session = sessionmaker()
session = Session(bind=engine)


class Page(Base):
    __tablename__ = 'bookpages'
    _id = Column(Integer, primary_key=True)
    id = Column(String(16), index=True)
    url = Column(String(1024))
    title = Column(String(256))

    @classmethod
    def create(cls, book):
        page = cls()
        page.id = book['id']
        page.url = book['url']
        page.title = book['title']
        return page

    @classmethod
    def is_existed(cls, _id):
        q = session.query(cls.id).filter(cls.id == _id).all()
        return len(q) > 0

    @classmethod
    def query_all(cls):
        return session.query(cls).all()


class Volume(Base):
    __tablename__ = 'bookvolumes'
    _id = Column(Integer, primary_key=True)
    id = Column(String(16), index=True)
    author = Column(String(64))
    title = Column(String(256))
    bookid = Column(String(16))
    pageurl = Column(String(256))
    exts = relationship("VolumeExt", backref="volume")

    @classmethod
    def create(cls, volume):
        vol = cls()
        vol.id = volume['id']
        vol.author = volume['author']
        vol.title = volume['title']
        vol.bookid = volume['bookid']
        vol.pageurl = volume['pageurl']

        for ext in volume['exts']:
            extend = VolumeExt()
            extend.volumetype = ext['type']
            extend.link = ext['link']
            vol.exts.append(extend)

        return vol

    @classmethod
    def is_existed(cls, _id):
        q = session.query(cls.id).filter(cls.id == _id).all()
        return len(q) > 0

    @classmethod
    def query_all(cls):
        return session.query(cls).all()

    @classmethod
    def query_by_title_or_author(cls, q):
        results = session.query(cls).filter(
            or_(cls.title.like('%{}%'.format(q)),
                cls.author.like('%{}%'.format(q)))).order_by(cls.title).all()
        return results

    @classmethod
    def _query(cls, q=None):
        if q:
            qry = session.query(cls).filter(
                or_(cls.title.like('%{}%'.format(q)),
                    cls.author.like('%{}%'.format(q)))).order_by(cls.title)
        else:
            qry = session.query(cls)

        return qry

    @classmethod
    def query(cls, q=None):
        qry = cls._query(q)
        return qry.all()

    @classmethod
    def query_by_id(cls, _id):
        qry = session.query(cls).filter(cls.id == _id).first()
        return qry

    @classmethod
    def count(cls):
        return session.query(func.count(cls.id)).scalar()

    def __json__(self, exluded_keys=set()):
        obj = super(Volume, self).__json__()
        if '_id' in obj:
            del obj['_id']
        exts = [ext.__json__() for ext in self.exts]
        for ext in exts:
            if '_id' in ext:
                del ext['_id']
        obj['exts'] = exts
        return obj

    @classmethod
    def query_as_pagination(cls, q=None, page=1, per_page=20):
        qry = cls._query(q)
        items = qry.offset((page-1)*per_page).limit(per_page).all()
        return Pagination(page, per_page, qry.count(), items)


class VolumeExt(Base):
    __tablename__ = 'volumeexts'
    _id = Column(Integer, primary_key=True)
    volumeid = Column(Integer, ForeignKey('bookvolumes._id'))
    volumetype = Column(String(8))
    link = Column(String(256))


Base.metadata.create_all(bind=engine)
