
---

# Book Management System

This project is built with **FastAPI** and provides functionality for managing books: creating, editing, deleting, and bulk importing. It also includes basic user authorization (registration, login) and automatically generated API documentation.

---

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/IraMladanovych02/BookManagement.git
   cd BookManagement
   ```

2. **Create and activate a virtual environment** (optional but recommended):

   - **Linux/Mac**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure `.env`** (if needed) with your environment variables:
   ```ini
   DB_HOST=db_host
   DB_PORT=db_port
   DB_USER=db_user
   DB_PASSWORD=password
   DB_NAME=db_name
   SECRET_KEY=some-secret-key
   ```
   Adjust these values according to your local setup.

---

## Running the Project

There are two main ways to start the FastAPI application:

1. **Using Uvicorn (recommended)**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```
   The app will be available at [http://127.0.0.1:8080](http://127.0.0.1:8080).

2. **Directly via `main.py`**:
   ```bash
   python main.py
   ```
   In the file `main.py`, there is typically:
   ```python
   if __name__ == "__main__":
       uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
   ```
   which is essentially the same as running the `uvicorn` command above.

---

## Database Migrations

1. **Check or update `alembic.ini`** so that `sqlalchemy.url` points to your database:
   ```ini
   sqlalchemy.url = postgresql://DB_USER:DB_PASS@DB_HOST:DB_PORT/DB_NAME
   ```
2. **Apply migrations**:
   ```bash
   alembic upgrade head
   ```
3. **Creating a new migration** after modifying models:
   ```bash
   alembic revision --autogenerate -m "Some changes"
   alembic upgrade head
   ```

---

## API Documentation

FastAPI automatically generates **Swagger** and **Redoc** documentation:

- **Swagger UI**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

---

## Key Endpoints

Below are some core endpoints defined in `main.py`:

- **`GET /books/`**  
  Returns a list of books with optional filters (title, author, genre, etc.) and pagination (skip, limit).

- **`POST /books/`**  
  Creates a new book.  
  Requires a valid JWT token (authorization).  
  Request body: `schemas.BookCreate`.

- **`GET /books/{book_id}`**  
  Retrieves a specific book by ID.

- **`PUT /books/{book_id}`**  
  Updates an existing book by ID.  
  Requires authorization.

- **`DELETE /books/{book_id}`**  
  Deletes a book by ID.  
  Requires authorization.

- **`POST /books/bulk`**  
  Allows bulk import of books from JSON or CSV files.  
  Requires authorization.

- **`POST /register`**  
  Registers a new user (requires `schemas.UserCreate`).

- **`POST /login`**  
  Authenticates a user and returns an `access_token`.

---

What`s to improve in this code:
1. Break down the logic of large files and numerous lines of code into smaller, more manageable modules.
2. Cover the code with integration tests



**Enjoy using the Book Management System!**