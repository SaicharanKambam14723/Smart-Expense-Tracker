import sqlite3

DB_NAME = "instance/expenses.db"

def get_db():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT UNIQUE,
        amount REAL NOT NULL
    )''')

    conn.commit()
    conn.close()