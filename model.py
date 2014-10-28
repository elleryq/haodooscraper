# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


db_url = os.environ.get("OPENSHIFT_MYSQL_DB_URL", "")

if not db_url:
    raise Exception("Need to set 'OPENSHIFT_MYSQL_DB_URL'.")

db_url = db_url.replace("mysql://", "mysql+pymysql://")
db_url = db_url + "?charset=utf8"
engine = create_engine(db_url)
Base = declarative_base()
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
    exts = relationship("VolumeExt", backref="volume")

    @classmethod
    def create(cls, volume):
        vol = cls()
        vol.id = volume['id']
        vol.author = volume['author']
        vol.title = volume['title']
        vol.bookid = volume['bookid']

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


class VolumeExt(Base):
    __tablename__ = 'volumeexts'
    _id = Column(Integer, primary_key=True)
    volumeid = Column(Integer, ForeignKey('bookvolumes._id'))
    volumetype = Column(String(8))
    link = Column(String(256))


Base.metadata.create_all(bind=engine)
