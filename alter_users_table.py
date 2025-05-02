import sqlite3

DB_PATH = 'papers.db'  # 請確認你的資料庫檔名正確

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    conn.commit()
    print("✅ 成功新增 display_name 欄位！")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ display_name 欄位已存在，無需重複新增。")
    else:
        print(f"❌ 發生錯誤：{e}")
finally:
    conn.close()
