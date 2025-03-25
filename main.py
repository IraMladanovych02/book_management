import uvicorn
from fastapi import (
    FastAPI,
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File
)
from sqlalchemy.orm import Session
from typing import List, Optional

import schemas
import crud
from db.engine import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm
from auth import get_current_user, verify_password, create_access_token

from db.models import DBUsers

app = FastAPI(
    title="Book Management System",
    description="API for managing books, authors, etc.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/myopenapi.json"
)

router = APIRouter()


@app.get("/")
def root():
    return {"message": "Welcome to the Book Management System"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/books/", response_model=List[schemas.Book])
def retrieve_all_books(
    title: Optional[str] = Query(None, description="Filter by book title"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    genre: Optional[schemas.Genres] = Query(None, description="Filter by genre"),
    year_from: Optional[int] = Query(None, description="Publication year from"),
    year_to: Optional[int] = Query(None, description="Publication year to"),
    skip: int = Query(0, ge=0, description="Skip N records for pagination"),
    limit: int = Query(10, gt=0, description="Number of records to display"),
    sort_by: Optional[str] = Query("title", description="Field to sort by (title, published_year, author)"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    try:
        books = crud.get_filtered_books(
            db,
            title=title,
            author=author,
            genre=genre,
            year_from=year_from,
            year_to=year_to,
            skip=skip,
            limit=limit
        )
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving books: {str(e)}")


@router.post("/books/", response_model=schemas.Book)
def create_new_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        return crud.create_book(db=db, book=book)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the book: {str(e)}")


@router.get("/books/{book_id}", response_model=schemas.Book)
def retrieve_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = crud.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookUpdate, db: Session = Depends(get_db)):
    book_data = book.dict(exclude_unset=True)
    updated_book = crud.update_book(db, book_id, book_data)
    return updated_book


@router.delete("/books/{book_id}", response_model=dict)
def delete_book(book_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        if not crud.delete_book(db, book_id):
            raise HTTPException(status_code=404, detail="Book not found")
        return {"detail": "Book deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the book: {str(e)}")


@router.post("/books/bulk", response_model=List[schemas.Book])
async def bulk_import_books(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        if file.content_type == "application/json":
            import json
            contents = await file.read()
            try:
                data = json.loads(contents)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON file")
            books = []
            for book_data in data:
                try:
                    book = schemas.BookCreate(**book_data)
                except Exception:
                    continue
                db_book = crud.create_book(db, book)
                books.append(db_book)
            return books
        elif file.content_type in ["text/csv", "application/vnd.ms-excel"]:
            import csv
            import io
            contents = await file.read()
            decoded = contents.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            books = []
            for row in reader:
                try:
                    book = schemas.BookCreate(
                        title=row.get("title", ""),
                        published_year=int(row.get("published_year", 0)),
                        genre=row.get("genre"),
                        author={"name": row.get("author_name", "")}
                    )
                except Exception:
                    continue
                db_book = crud.create_book(db, book)
                books.append(db_book)
            return books
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during bulk import: {str(e)}")


@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@router.post("/users/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(DBUsers).filter(DBUsers.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
