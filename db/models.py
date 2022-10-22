from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    func,
    SmallInteger,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class PublishHistory(Base):
    __tablename__ = "publish_history"

    id = Column(BigInteger, primary_key=True)
    page_id = Column(Integer)
    message_id = Column(BigInteger)


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

    id = Column(Integer, primary_key=True, autoincrement=False)
    type = Column(String)
    data = Column(String)
