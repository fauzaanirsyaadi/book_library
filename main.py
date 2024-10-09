from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Literal
from sqlalchemy import Boolean, create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import re  
import bcrypt 
from datetime import datetime  
import logging

# Setup database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)

class BookDB(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_borrowed = Column(Boolean, default=False)

class LoanDB(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    borrowed_at = Column(DateTime, default=datetime.utcnow)  # Tanggal peminjaman
    returned_at = Column(DateTime, nullable=True)  # Tanggal pengembalian

# Buat tabel di database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Buku",
    description="API untuk manajemen buku dan pengguna.",
    version="1.0.0",
)

# Model untuk pendaftaran pengguna
class User(BaseModel):
    email: EmailStr
    password: str
    role: Literal["admin", "borrower"] 
    
    @field_validator('email')
    def validate_email_domain(cls, value):
        allowed_domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]
        if not any(value.endswith(f"@{domain}") for domain in allowed_domains):
            raise ValueError(f"Email must be one of the following domains: {', '.join(allowed_domains)}")
        return value
    
    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"^[A-Za-z0-9]+$", value):
            raise ValueError("Password must be alphanumeric and cannot contain special characters.")
        return value
    
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    def validate_email_domain(cls, value):
        allowed_domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"]
        if not any(value.endswith(f"@{domain}") for domain in allowed_domains):
            raise ValueError(f"Email must be one of the following domains: {', '.join(allowed_domains)}")
        return value
    
    @field_validator('password')
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"^[A-Za-z0-9]+$", value):
            raise ValueError("Password must be alphanumeric and cannot contain special characters.")
        return value

class Book(BaseModel):
    id: int
    title: str
    author: str
    description: str = None

    class Config:
        from_attributes = True 

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    description: str = None
    is_borrowed: bool

    class Config:
        from_attributes = True 

class LoanResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrowed_at: datetime
    returned_at: datetime = None

    class Config:
        from_attributes = True 

class BookCreate(BaseModel):
    title: str
    author: str
    description: str = None

class BookUpdate(BaseModel):
    title: str = None
    author: str = None
    description: str = None

# Fungsi untuk mendapatkan sesi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logging.basicConfig(level=logging.INFO)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "message": "An error occurred."},
    )

@app.get("/")
def read_root():
    return {"message": "Server is running"}


@app.post("/register", response_model=User)
def register_user(user: User, db: Session = Depends(get_db)):
    # Memeriksa apakah email sudah terdaftar
    if db.query(UserDB).filter(UserDB.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    db_user = UserDB(email=user.email, password=hashed_password.decode('utf-8'), role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Register berhasil"}

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # Memeriksa apakah pengguna ada
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user.password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Kredensial tidak valid")
    return {"message": "Login berhasil"}


@app.get("/books", response_model=List[BookResponse])  # Endpoint untuk mendapatkan daftar buku
def get_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = db.query(BookDB).offset(skip).limit(limit).all()
    return books

@app.post("/borrow")
def borrow_book(user_email: str, book_id: int, db: Session = Depends(get_db)):
    # Cek apakah pengguna sudah meminjam buku lain
    current_borrowed_book = db.query(BookDB).filter(BookDB.user_id == user_email, BookDB.is_borrowed == True).first()
    if current_borrowed_book:
        raise HTTPException(status_code=400, detail="Anda sudah meminjam buku lain. Kembalikan buku terlebih dahulu.")

    # Cek apakah buku yang ingin dipinjam ada dan tidak sedang dipinjam
    book = db.query(BookDB).filter(BookDB.id == book_id, BookDB.is_borrowed == False).first()
    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan atau sedang dipinjam.")

    # Update status peminjaman
    book.is_borrowed = True
    book.user_id = user_email  # Simpan ID pengguna yang meminjam
    db.commit()

    # Catat peminjaman
    loan_record = LoanDB(user_id=user_email, book_id=book_id)
    db.add(loan_record)
    db.commit()
    
    return {"message": f"Pengguna {user_email} meminjam buku {book.title}"}

@app.post("/return")
def return_book(user_email: str, book_id: int, db: Session = Depends(get_db)):
    # Cek apakah buku yang ingin dikembalikan ada dan dipinjam oleh pengguna
    book = db.query(BookDB).filter(BookDB.id == book_id, BookDB.user_id == user_email, BookDB.is_borrowed == True).first()
    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan atau tidak dipinjam oleh Anda.")

    # Update status peminjaman
    book.is_borrowed = False
    book.user_id = None  # Reset ID pengguna
    db.commit()

    # Update catatan peminjaman dengan tanggal pengembalian
    loan_record = db.query(LoanDB).filter(LoanDB.user_id == user_email, LoanDB.book_id == book_id, LoanDB.returned_at == None).first()
    if loan_record:
        loan_record.returned_at = datetime.utcnow()  # Set tanggal pengembalian
        db.commit()
    
    return {"message": f"Buku {book.title} telah dikembalikan."}

# Function to get the current user (for authentication)
def get_current_user(user_email: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def admin_required(user: UserLogin = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only.")
    

@app.get("/loans", response_model=List[LoanResponse])  # Endpoint for admin to check loan status
def get_loans(db: Session = Depends(get_db), user: UserLogin = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only.")
    
    loans = db.query(LoanDB).filter(LoanDB.returned_at == None).all()  # Get all active loans
    return loans

@app.post("/books", response_model=BookResponse)  # Endpoint for creating a new book
def create_book(book: BookCreate, db: Session = Depends(get_db), user: UserLogin = Depends(admin_required)):
    logging.info(f"Admin {user.email} is creating a book: {book.title}")
    
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only.")
    
    new_book = BookDB(**book.dict())
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@app.put("/books/{book_id}", response_model=BookResponse)  # Endpoint for updating a book
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), user: UserLogin = Depends(admin_required)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only.")
    
    db_book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found.")
    
    for key, value in book.dict(exclude_unset=True).items():
        setattr(db_book, key, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", response_model=dict)  # Endpoint for deleting a book
def delete_book(book_id: int, db: Session = Depends(get_db), user: UserLogin = Depends(admin_required)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only.")
    
    db_book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found.")
    
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully."}