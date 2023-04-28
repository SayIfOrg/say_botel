from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    func,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Content(Base):
    __tablename__ = "content"

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    page_id = Column(Integer)

    @property
    def message_id(self):
        return self.id


class BlogRegistered(Base):
    __tablename__ = "blog_registered"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat.id"))
    project_oid = Column(Integer)
    created_by_chat = Column(Integer, ForeignKey("chat.id"))
    created_by_oid = Column(Integer)
    create_date = Column(DateTime, server_default=func.now())

    __mapper_args__ = {"eager_defaults": True}


class Chat(Base):
    __tablename__ = "chat"

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    type = Column(String, nullable=False)
    data = Column(String)
    linked_chat_id = Column(BigInteger, ForeignKey("chat.id"), unique=True)


class Commentable(Base):
    __tablename__ = "commentable"

    id = Column(BigInteger, primary_key=True)
    group_id = Column(BigInteger, ForeignKey("chat.id"), nullable=False)
    content_id = Column(BigInteger, ForeignKey("content.id"), nullable=False)


class Bot(Base):
    __tablename__ = "bot"
    id = Column(Integer, primary_key=True)
    api_token = Column(String)
    site_id = Column(Integer, nullable=False)
