import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = 'papers.db'  # 請確認資料庫路徑正確

# 要新增的管理員帳號資訊
new_username = 'admin'
new_password = 'admin123'  # 可以換成你要的新密碼
new_role = 'admin'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (new_username, generate_password_hash(new_password), new_role)
    )
    conn.commit()
    print(f"✅ 成功新增管理員帳號 {new_username}")
except sqlite3.IntegrityError:
    print(f"⚠️ 帳號 {new_username} 已存在，無法新增")
finally:
    conn.close()
