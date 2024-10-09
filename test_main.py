import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends

# Setup the database for testing
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency override for testing
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    # Create a test user
    response = client.post("/register", json={"email": "testuser@gmail.com", "password": "TestPassword1", "role": "admin"})
    assert response.status_code == 200
    return response.json()

def test_login(test_user):
    # Test user login
    response = client.post("/login", json={"email": "testuser@gmail.com", "password": "TestPassword1"})
    assert response.status_code == 200
    assert response.json() == {"message": "Login berhasil"}

def test_create_book(test_user):
    # Test creating a book
    response = client.post("/books", json={"title": "Test Book", "author": "Test Author", "description": "Test Description"}, headers={"Authorization": "Bearer testuser@gmail.com"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"

def test_update_book(test_user):
    # Test updating the book
    response = client.put("/books/1", json={"title": "Updated Test Book"}, headers={"Authorization": "Bearer testuser@gmail.com"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Test Book"

def test_delete_book(test_user):
    # Test deleting the book
    response = client.delete("/books/1", headers={"Authorization": "Bearer testuser@gmail.com"})
    assert response.status_code == 200
    assert response.json() == {"message": "Book deleted successfully."}