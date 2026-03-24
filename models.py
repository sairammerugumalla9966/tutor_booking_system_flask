import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        is_approved INTEGER DEFAULT 0
    )
    ''')

    # Slots table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tutor_id INTEGER,
        date TEXT,
        time TEXT,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY (tutor_id) REFERENCES users (id)
    )
    ''')

    # Bookings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        tutor_id INTEGER,
        slot_id INTEGER,
        status TEXT,
        FOREIGN KEY (student_id) REFERENCES users (id),
        FOREIGN KEY (tutor_id) REFERENCES users (id),
        FOREIGN KEY (slot_id) REFERENCES slots (id)
    )
    ''')

    conn.commit()
    conn.close()
