import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = 'papers.db'  # 請依你實際資料庫位置修改

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 建立 users 資料表
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

# 插入預設帳號（admin 與 user 各一）
users = [
    ('admin', generate_password_hash('admin123'), 'admin'),
    ('alice', generate_password_hash('alicepass'), 'user')
]

for u in users:
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", u)
    except sqlite3.IntegrityError:
        print(f"帳號 {u[0]} 已存在，略過。")

conn.commit()
conn.close()
print("✅ users 資料表建立完成，並匯入初始帳號")
