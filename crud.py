import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from db import models
from schemas import BookCreate, UserCreate
from db.models import DBUsers, DBBooks, DBAuthors
from auth import get_password_hash, verify_password

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_user(db: Session, user: UserCreate):
    """
        Create a new user in the database.

        Parameters:
            db (Session): The SQLAlchemy database session.
            user (UserCreate): The user data to create, including username and password.

        Returns:
            DBUsers: The created user object.

        Raises:
            HTTPException: If the username is already registered.
    """
    logger.debug("Attempting to create a new user with username: %s", user.username)
    existing_user = db.query(DBUsers).filter(DBUsers.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = DBUsers(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    logger.info("User created successfully with username: %s", user.username)
    return db_user


def authenticate_user(db: Session, username: str, password: str):
    """
        Authenticate a user by checking the username and password.

        Parameters:
            db (Session): The SQLAlchemy database session.
            username (str): The username of the user.
            password (str): The password provided for authentication.

        Returns:
            DBUsers or None: The authenticated user object if credentials are valid; otherwise, None.
    """
    logger.debug("Authenticating user with username: %s", username)
    user = db.query(DBUsers).filter(DBUsers.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("Authentication failed")
        return None
    logger.info("User '%s' authenticated successfully", username)
    return user


def get_all_books(db: Session):
    """
        Retrieve all books from the database.
        Parameters:
            db (Session): The SQLAlchemy database session.

        Returns:
            list[dict]: A list of dictionaries, each representing a book record.

        Raises:
            HTTPException: If an error occurs while retrieving books.
    """
    logger.debug("Retrieving all books from the database.")
    try:
        result = db.execute(text("SELECT * FROM books"))
        rows = result.fetchall()
        logger.info("Successfully retrieved %d books.", len(rows))
        return [dict(row) for row in rows]
    except Exception as e:
        db.rollback()
        logger.error("Error retrieving books: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving books: {str(e)}")


def get_filtered_books(db: Session, title: str, author: str, genre: str, year_from: int, year_to: int, skip: int, limit: int):
    """
        Retrieve books from the database based on filter criteria.
        Parameters:
            db (Session): The SQLAlchemy database session.
            title (str): A substring to match in the book title.
            author (str): A substring to match in the author's name.
            genre (str): The genre of the book (converted to uppercase).
            year_from (int): The starting year for filtering the published year.
            year_to (int): The ending year for filtering the published year.
            skip (int): The number of records to skip (offset).
            limit (int): The maximum number of records to return.
        Returns:
            list[dict]: A list of dictionaries, each representing a filtered book record.
    """
    query = text("""
        SELECT * FROM books
        WHERE title ILIKE :title
          AND author ILIKE :author
          AND genre = :genre
          AND published_year BETWEEN :year_from AND :year_to
        LIMIT :limit OFFSET :skip
    """)
    params = {
        "title": f"%{title}%",
        "author": f"%{author}%",
        "genre": genre.upper(),
        "year_from": year_from,
        "year_to": year_to,
        "limit": limit,
        "skip": skip,
    }
    result = db.execute(query, params)
    rows = result.fetchall()
    logger.info("Filtered books retrieved: %d records found.", len(rows))
    return [dict(row) for row in rows]


def create_book(db: Session, book):
    """
    Create a new book record in the database.

    Parameters:
        db (Session): SQLAlchemy session object.
        book (Union[dict, BookCreate]): Data for the new book.
    Returns:
        dict: A dictionary containing the created book's details.
    Raises:
        HTTPException: If an error occurs during the book creation process.
    """
    try:
        logger.debug("Starting creation of a new book.")
        book_data = book.dict(exclude_unset=True) if not isinstance(book, dict) else book

        new_book = models.DBBooks(
            title=book_data.get("title"),
            published_year=book_data.get("published_year"),
            genre=book_data.get("genre").upper() if isinstance(book_data.get("genre"), str) else book_data.get("genre"),
            author=book_data.get("author_name")
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        logger.info(f"Book created with ID: {new_book.id}")

        return {
            "id": new_book.id,
            "title": new_book.title,
            "author": new_book.author,
            "genre": new_book.genre,
            "published_year": new_book.published_year
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating book: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating book: {str(e)}")


def update_book(db: Session, book_id: int, book):
    """
    Update an existing book record in the database by book_id.

    Parameters:
        db (Session): SQLAlchemy session object.
        book_id (int): The ID of the book to update.
        book (Union[dict, BookCreate/BookUpdate]): Data for updating the book.

    Returns:
        dict: A dictionary containing the updated book's details.

    Raises:
        HTTPException: If the book is not found or if an error occurs during the update process.
    """
    try:
        logger.debug(f"Starting update for book with ID: {book_id}")
        # Convert the Pydantic model to a dict if necessary
        book_data = book.dict(exclude_unset=True) if not isinstance(book, dict) else book

        title = book_data.get("title")
        author_name = book_data.get("author_name")
        genre = book_data.get("genre")
        published_year = book_data.get("published_year")

        if isinstance(genre, str):
            genre_value = genre.upper()
        elif genre is not None:
            genre_value = genre.value
        else:
            genre_value = None

        query = text("""
            UPDATE books
            SET title = :title,
                author = :author,
                genre = :genre,
                published_year = :published_year
            WHERE id = :id
            RETURNING id, title, author, genre, published_year
        """)
        params = {
            "title": title,
            "author": author_name,
            "genre": genre_value,
            "published_year": published_year,
            "id": book_id
        }
        result = db.execute(query, params)
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Book not found")
        db.commit()
        logger.info(f"Book with ID: {book_id} updated successfully.")
        return dict(row)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating book with ID {book_id}: {str(e)}", exc_info=True)

        raise HTTPException(status_code=500, detail=f"Error updating book: {str(e)}")


def get_book_by_id(db: Session, book_id: int):
    """
        Retrieve a book record from the database by its ID.

        Parameters:
            db (Session): The SQLAlchemy database session.
            book_id (int): The ID of the book to retrieve.

        Returns:
            dict or None: A dictionary representing the book record if found; otherwise, None.

        Raises:
            HTTPException: If an error occurs during retrieval.
    """
    logger.debug("Attempting to retrieve book with ID: %d", book_id)
    try:
        query = text("SELECT * FROM books WHERE id = :id")
        result = db.execute(query, {"id": book_id})
        row = result.fetchone()
        logger.info("Book with ID %d found.", book_id)
        return dict(row) if row else None
    except Exception as e:
        db.rollback()
        logger.error("Error retrieving book by ID %d: %s", book_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving book by id: {str(e)}")


def delete_book(db: Session, book_id: int):
    """
        Delete a book record from the database by its ID.

        Parameters:
            db (Session): The SQLAlchemy database session.
            book_id (int): The ID of the book to delete.

        Returns:
            bool: True if the book was deleted successfully; False otherwise.

        Raises:
            HTTPException: If an error occurs during deletion.
    """
    logger.debug("Attempting to delete book with ID: %d", book_id)
    try:
        query = text("DELETE FROM books WHERE id = :id")
        result = db.execute(query, {"id": book_id})
        db.commit()
        logger.info("Book with ID %d deleted successfully.", book_id)
        return result.rowcount == 1
    except Exception as e:
        db.rollback()
        logger.error("Error deleting book with ID %d: %s", book_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
