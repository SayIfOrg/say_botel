from typing import Counter
from sqlalchemy import Column, DateTime, ForeignKey, Integer, BigInteger, String, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class PublishHistory(Base):
    __tablename__ = "publish_history"

    id = Column(BigInteger, primary_key=True)
    page_id = Column(Integer)
    message_id = Column(BigInteger)


class A(Base):
    __tablename__ = "a"

    id = Column(Integer, primary_key=True)
    data = Column(String)
    create_date = Column(DateTime, server_default=func.now())
    bs = relationship("B")

    # required in order to access columns with server defaults
    # or SQL expression defaults, subsequent to a flush, without
    # triggering an expired load
    __mapper_args__ = {"eager_defaults": True}


class B(Base):
    __tablename__ = "b"
    id = Column(Integer, primary_key=True)
    a_id = Column(ForeignKey("a.id"))
    data = Column(String)
