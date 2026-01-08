import sqlite3
import os

DB_PATH = "chat_history/chatbot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists("chat_history"):
        os.makedirs("chat_history")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Session Table
    # Columns: Session ID (Primary Key) UUID, User Id, Date, Time, Title (Suggestion), Updated At (Suggestion)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Session (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            title TEXT,
            updated_at TEXT
        )
    ''')
    
    # Session Information Table
    # Columns: Session ID (foreign key), Question, Response, Time, Date, Metadata (Suggestion for rich data)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SessionInformation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT,
            response TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            response_metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES Session (session_id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
