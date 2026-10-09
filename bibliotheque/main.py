from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Bibliothèque 3-Tiers API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la base de données via les variables d'environnement
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "library")
DB_USER = os.getenv("DB_USER", "admin_db")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secure_password_123")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    """Tente de se connecter à la base de données et crée la table books si elle n'existe pas."""
    retries = 5
    while retries > 0:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    year INT
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Base de données initialisée avec succès.")
            return
        except Exception as e:
            retries -= 1
            print(f"Base de données non disponible, nouvelle tentative dans 3 secondes... ({retries} essais restants). Erreur : {e}")
            time.sleep(3)
    print("Avertissement : Impossible d'initialiser la base de données au démarrage.")

@app.on_event("startup")
def startup_event():
    init_db()

class BookCreate(BaseModel):
    title: str
    author: str
    year: int

@app.get("/api/books")
def get_books():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, author, year FROM books ORDER BY id DESC;")
        books = cur.fetchall()
        cur.close()
        conn.close()
        return books
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/books", status_code=201)
def add_book(book: BookCreate):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, author, year) VALUES (%s, %s, %s) RETURNING id, title, author, year;",
            (book.title, book.author, book.year)
        )
        new_book = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return new_book
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM books WHERE id = %s RETURNING id;", (book_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if not deleted:
            raise HTTPException(status_code=404, detail="Livre introuvable")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Monter le front-end statique
app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")