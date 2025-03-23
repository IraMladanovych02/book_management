import datetime
from enum import StrEnum, auto
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship, validates

from db.engine import Base


class Genres(StrEnum):
    FICTION = auto()
    NONFICTION = auto()
    SCIENCE = auto()
    HISTORY = auto()
    FANTASY = auto()
    ROMANCE = auto()
    AUTOBIOGRAPHY = auto()


class DBAuthors(Base):
    __tablename__ = 'authors'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)


class DBBooks(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    genre = Column(Enum(Genres))
    published_year = Column(Integer)
    authors_id = Column(Integer, ForeignKey('authors.id'))
    authors = relationship(DBAuthors)

    @validates('published_year')
    def validate_published_year(self, key, value):
        current_year = datetime.datetime.now().year
        if value < 1800 or value > current_year:
            raise ValueError(f"published_year must be between 1800 and {current_year}")
        return value


class DBUsers(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
