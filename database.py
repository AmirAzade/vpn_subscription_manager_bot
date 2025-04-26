import sqlite3

# Connect to SQLite
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

# Create users table
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id TEXT UNIQUE,
    subscription_end_date TEXT,
    configs TEXT,
    subs TEXT,
    invite_code TEXT UNIQUE
)
''')
conn.commit()
