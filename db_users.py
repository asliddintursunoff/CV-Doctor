# db.py
import sqlite3

def init_db():
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            phone TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user(telegram_id, first_name, last_name, username, phone):
    conn = sqlite3.connect("bot_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (telegram_id, first_name, last_name, username, phone)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, first_name, last_name, username, phone))
    conn.commit()
    conn.close()
