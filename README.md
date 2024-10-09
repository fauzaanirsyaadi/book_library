# book_library
feature :
**Register and Login**
- Email     : validation email (@gmail.com, @hotmail.com, etc)
- Password  : password harus terdiri dari 8 Karakter Alphanumeric dan harus mengandung setidaknya 1 huruf kapital, tidak boleh mengandung special karakter
- tidak dapat register dengan email yang sama.

**Management**
1. Terdapat fungsi yang berguna untuk mencatat peminjaman buku
2. Admin Perpustakaan dapat mengetahui bahwa buku telat dikembalikan atau masih dalam peminjaman
3. Setiap user hanya bisa meminjam 1 buku dan apabila sedang meminjam buku harus dikembalikan terlebih dahulu agar dapat meminjam Kembali


project ini menggunakan :
- FastAPI
- SQLAlchemy
- Alembic
- Bcrypt
- Email-validator
- Pytest
- Httpx 


**HOW TO RUN**
virtual env :
   python -m venv venv
   venv\Scripts\activate

requirement :
   pip install fastapi uvicorn
   pip install email-validator
   pip install sqlalchemy
   pip install alembic
   pip install bcrypt
   pip install pytest httpx

run server:
   uvicorn main:app --reload

run test :
   pytest test_main.py

**SQL**
INSERT INTO books (title, author, description, user_id) VALUES
('Judul Buku 1', 'Penulis 1', 'Deskripsi Buku 1', 1),
('Judul Buku 2', 'Penulis 2', 'Deskripsi Buku 2', 1),
('Judul Buku 3', 'Penulis 3', 'Deskripsi Buku 3', 2);

**API Documentation**
http://127.0.0.1:8000/docs




