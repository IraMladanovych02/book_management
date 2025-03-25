import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, validator


class Genres(str, Enum):
    FICTION = "FICTION"
    NONFICTION = "NONFICTION"


class AuthorBase(BaseModel):
    name: str

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty")
        return v


class Author(AuthorBase):
    id: int

    class Config:
        from_attributes = True


class BookBase(BaseModel):
    title: str
    published_year: int
    genre: Genres

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @validator('published_year')
    def valid_published_year(cls, v):
        current_year = datetime.datetime.now().year
        if v < 1800 or v > current_year:
            raise ValueError(f"The published year must be from 1800 to {current_year}")
        return v


class BookCreate(BookBase):
    title: str
    published_year: int
    author_name: str
    genre: Genres

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @validator('published_year')
    def valid_published_year(cls, v):
        current_year = datetime.datetime.now().year
        if v < 1800 or v > current_year:
            raise ValueError(f"The published year must be from 1800 to {current_year}")
        return v


class Book(BookBase):
    id: int
    author: Author

    class Config:
        from_attributes = True


class BookUpdate(BaseModel):
    title: Optional[str] = None
    published_year: Optional[int] = None
    genre: Optional[Genres] = None
    author_name: Optional[str] = None

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @validator('published_year')
    def valid_published_year(cls, v):
        if v is not None:
            current_year = datetime.datetime.now().year
            if v < 1800 or v > current_year:
                raise ValueError(f"The published year must be from 1800 to {current_year}")
        return v


class UserCreate(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Username cannot be empty")
        return v

    @validator('password')
    def password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
