from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import Field, SQLModel, Session, create_engine, select
from fastapi.exceptions import HTTPException


class BookBase(SQLModel):
    title: str = Field(index=True)
    author: str
    isbn: str = Field(min_length=4, max_length=5, default="0011")
    description: Optional[str]


class Book(BookBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


URL_DATABASE = "postgresql://postgres:Neevan.m%4013@localhost:5432/Book"
# connect_args = {"check_same_thread": False}
engine = create_engine(
    URL_DATABASE,
    echo=True,
)


def create_db_and_table():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup():
    create_db_and_table()


@app.post("/")
async def create_book(book: Book, session=Depends(get_session)):

    db_item = book
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.get("/books", response_model=list[Book])
async def read_books(session=Depends(get_session)):
    # select * from table
    books = session.exec(select(Book)).all()
    return books


@app.get("/books/{book_id}", response_model=Book)
async def read_book(book_id: int, session=Depends(get_session)):

    book_item = session.get(Book, book_id)
    if not book_item:
        raise HTTPException(status_code=404, detail="Book not found")
    return book_item


@app.patch("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, book: Book, session=Depends(get_session)):

    book_item = session.get(Book, book_id)
    if not book_item:
        raise HTTPException(status_code=404, detail="Book not found")
    book_data = book.dict(exclude_unset=True)
    for key, value in book_data.items():
        setattr(book_item, key, value)
    session.add(book_item)
    session.commit()
    session.refresh(book_item)
    return book_item


@app.delete("/books/{book_id}")
async def delete_book(book_id: int, session=Depends(get_session)):
    book_item = session.get(Book, book_id)
    if not book_item:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book_item)
    session.commit()
    return {"Deleted": True}
