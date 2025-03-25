import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from crud import get_filtered_books, delete_book, update_book, create_book
from schemas import BookCreate, AuthorBase


def test_get_filtered_books():
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.fetchall.return_value = [
        {"id": 1, "title": "Book 1", "author": "Author 1", "genre": "FICTION", "published_year": 2020},
        {"id": 2, "title": "Book 2", "author": "Author 2", "genre": "NONFICTION", "published_year": 2021},
    ]

    result = get_filtered_books(mock_db, title="Book", author="Author", genre="FICTION", year_from=2020, year_to=2022, skip=0, limit=10)

    assert len(result) == 2
    assert result[0]["title"] == "Book 1"
    mock_db.execute.assert_called_once()


def test_create_book():
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.fetchone.return_value = {
        "id": 1,
        "title": "New Book",
        "author": "New Author",
        "genre": "FICTION",
        "published_year": 2023
    }

    book_data = BookCreate(
        title="New Book",
        published_year=2023,
        genre="FICTION",
        author_name="New Author"
    )

    result = create_book(mock_db, book_data)

    assert result["title"] == "New Book"


def test_update_book():
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.fetchone.return_value = {
        "id": 1,
        "title": "Updated Book",
        "author": "Updated Author",
        "genre": "NONFICTION",
        "published_year": 2023
    }

    book_data = BookCreate(
        title="Updated Book",
        published_year=2023,
        genre="NONFICTION",
        author_name="Updated Author"
    )

    result = update_book(mock_db, book_id=1, book=book_data)
    assert result["title"] == "Updated Book"


def test_delete_book():
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.rowcount = 1

    result = delete_book(mock_db, book_id=1)

    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
