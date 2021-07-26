from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    imdb_id = Column(Integer)
    title = Column(String)
    year = Column(Integer)
    rating = Column(Float)
    watched = Column(Boolean)
