import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from schemas import BookCreate, UserCreate
from db.models import DBUsers
from auth import get_password_hash, verify_password


def create_user(db: Session, user: UserCreate):
    existing_user = db.query(DBUsers).filter(DBUsers.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = DBUsers(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(DBUsers).filter(DBUsers.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_all_books(db: Session):
    try:
        result = db.execute(text("SELECT * FROM books"))
        rows = result.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error retrieving books: {str(e)}")


def get_filtered_books(
    db: Session,
    title: str = None,
    author: str = None,
    genre = None,
    year_from: int = None,
    year_to: int = None,
    skip: int = 0,
    limit: int = 10,
    sort_by: str = "title",
    order: str = "asc"
):
    try:
        query_str = "SELECT * FROM books WHERE 1=1"
        params = {}
        if title:
            query_str += " AND title ILIKE :title"
            params["title"] = f"%{title}%"
        if author:
            query_str += " AND author ILIKE :author"
            params["author"] = f"%{author}%"
        if genre:
            query_str += " AND genre = :genre"
            params["genre"] = genre
        if year_from:
            query_str += " AND published_year >= :year_from"
            params["year_from"] = year_from
        if year_to:
            query_str += " AND published_year <= :year_to"
            params["year_to"] = year_to

        # Безпечне сортування
        if sort_by not in ["title", "published_year", "author"]:
            sort_by = "title"
        if order.lower() not in ["asc", "desc"]:
            order = "asc"
        query_str += f" ORDER BY {sort_by} {order.upper()}"

        query_str += " LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip

        result = db.execute(text(query_str), params)
        rows = result.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error filtering books: {str(e)}")


def get_book_by_id(db: Session, book_id: int):
    try:
        query = text("SELECT * FROM books WHERE id = :id")
        result = db.execute(query, {"id": book_id})
        row = result.fetchone()
        return dict(row) if row else None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error retrieving book by id: {str(e)}")


def create_book(db: Session, book: BookCreate):
    try:
        query_author = text("SELECT * FROM authors WHERE name = :name")
        result = db.execute(query_author, {"name": book.author.name})
        author_row = result.fetchone()
        if not author_row:
            insert_author = text("INSERT INTO authors (name) VALUES (:name) RETURNING id")
            result = db.execute(insert_author, {"name": book.author.name})
            new_author = result.fetchone()
            if not new_author:
                db.rollback()
                raise HTTPException(status_code=500, detail="Failed to create author")
            author_id = new_author["id"]
            db.commit()
        else:
            author_id = author_row["id"]

        insert_book = text("""
            INSERT INTO books (title, published_year, genre, author, author_id)
            VALUES (:title, :published_year, :genre, :author, :author_id)
            RETURNING *
        """)
        result = db.execute(insert_book, {
            "title": book.title,
            "published_year": book.published_year,
            "genre": book.genre,
            "author": book.author.name,
            "author_id": author_id
        })
        db.commit()
        new_book = result.fetchone()
        return dict(new_book) if new_book else None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating book: {str(e)}")


def update_book(db: Session, book_id: int, book: BookCreate):
    try:
        existing_book = get_book_by_id(db, book_id)
        if not existing_book:
            return None
        update_query = text("""
            UPDATE books
            SET title = :title, published_year = :published_year, genre = :genre, author = :author
            WHERE id = :id
            RETURNING *
        """)
        result = db.execute(update_query, {
            "title": book.title,
            "published_year": book.published_year,
            "genre": book.genre,
            "author": book.author.name,
            "id": book_id
        })
        db.commit()
        updated = result.fetchone()
        return dict(updated) if updated else None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating book: {str(e)}")


def delete_book(db: Session, book_id: int):
    try:
        existing_book = get_book_by_id(db, book_id)
        if not existing_book:
            return False
        delete_query = text("DELETE FROM books WHERE id = :id")
        db.execute(delete_query, {"id": book_id})
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
