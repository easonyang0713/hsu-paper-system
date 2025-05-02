import sqlite3

try:
    # 連接資料庫
    conn = sqlite3.connect('papers.db')
    cursor = conn.cursor()

    # 插入假資料
    sample_data = [
        (
            '人工智慧在教育領域的應用',
            '張三, 李四',
            '本研究探討人工智慧技術如何協助教學及學習。',
            '人工智慧, 教育科技',
            '台灣教育科技期刊',
            2023,
            '教育學, 資訊工程',
            'ai_in_education.pdf'
        ),
        (
            '區塊鏈技術於醫療資料管理之應用',
            '王五, 趙六',
            '本研究提出一種基於區塊鏈的醫療資料安全管理架構。',
            '區塊鏈, 醫療資訊',
            '國際醫療資訊研討會',
            2022,
            '醫學, 資訊工程',
            'blockchain_healthcare.pdf'
        )
    ]

    # 批次插入
    cursor.executemany('''
        INSERT INTO papers (title, authors, abstract, keywords, source, year, field, pdf_filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)

    conn.commit()
    print("✅ 假資料成功寫入 papers.db！")
except sqlite3.Error as e:
    print("❌ 發生錯誤：", e)
finally:
    if conn:
        conn.close()

conn.commit()
