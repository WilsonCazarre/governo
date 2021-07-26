from sqlalchemy import Column, Integer, String, Float, Date, BigInteger
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    imdb_id = Column(Integer)
    title = Column(String)
    year = Column(Integer)
    rating = Column(Float)
    guild_id = Column(BigInteger)
    watched_date = Column(Date, nullable=True)


class ConfigVariable(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    value = Column(String, nullable=True)
    guild_id = Column(String)
