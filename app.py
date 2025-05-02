from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash
import sqlite3
import os
from werkzeug.utils import secure_filename

# ✅ 初始化 Flask 應用
app = Flask(__name__)

# ✅ 設定檔案上傳目錄與 Session 金鑰
app.secret_key = os.getenv("SECRET_KEY")  # 用來加密 session 的金鑰（可自訂）
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'pdf')
DB_PATH = 'papers.db'  # 資料庫路徑

# ✅ 確保 PDF 資料夾存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ PDF 副檔名驗證
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def login_required():
    if not session.get('logged_in'):
        flash("⚠️ 請先登入才能瀏覽")
        return redirect(url_for('login'))
    return None

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/search')
def search():
    if not session.get('logged_in'):
        flash("請先登入才能搜尋")
        return redirect(url_for('login'))
    keyword = request.args.get('keyword', '').strip()
    scope = request.args.get('scope', 'all')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    keyword_lower = keyword.lower()

    if scope == 'all':
        query = """
        SELECT * FROM papers
        WHERE 
            LOWER(COALESCE(title, '')) LIKE ? OR 
            LOWER(COALESCE(authors, '')) LIKE ? OR 
            LOWER(COALESCE(source, '')) LIKE ?
        """
        params = (f"%{keyword_lower}%",) * 3
    else:
        query = f"""
        SELECT * FROM papers
        WHERE LOWER(COALESCE({scope}, '')) LIKE ?
        """
        params = (f"%{keyword_lower}%",)

    print("🟡 正在執行查詢 SQL：")
    print(query)
    print("🟡 查詢參數：", params)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    print(f"🟢 查詢結果筆數：{len(results)}")

    return render_template('search_results.html', results=results, keyword=keyword, scope=scope)
    
@app.route('/search/advanced', methods=['GET', 'POST'])
def advanced_search():
    if not session.get('logged_in'):
        flash("請先登入才能使用進階搜尋")
        return redirect(url_for('login'))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 抓所有研究領域名稱
    cursor.execute("SELECT * FROM fields ORDER BY name")
    fields = cursor.fetchall()

    if request.method == 'GET':
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ✅ 用這段代替舊的 SELECT * FROM fields
        cursor.execute("""
            SELECT f.* 
            FROM fields f
            WHERE EXISTS (
                SELECT 1 FROM paper_fields pf 
                WHERE pf.field_id = f.id
            )
            ORDER BY f.name
        """)
        fields = cursor.fetchall()

        conn.close()
        return render_template('advanced_search.html', fields=fields)


    # POST：搜尋處理
    keyword = request.form.get('keyword', '').strip().lower()
    keyword_field = request.form.get('keyword_field', '').strip().lower()
    start_year = request.form.get('start_year', '').strip()
    end_year = request.form.get('end_year', '').strip()
    selected_fields = request.form.getlist('field')

    query = "SELECT DISTINCT p.* FROM papers p LEFT JOIN paper_fields pf ON p.id = pf.paper_id LEFT JOIN fields f ON pf.field_id = f.id WHERE 1=1"
    params = []

    if keyword:
        query += " AND (LOWER(p.title) LIKE ? OR LOWER(p.authors) LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if start_year:
        query += " AND p.year >= ?"
        params.append(start_year)

    if end_year:
        query += " AND p.year <= ?"
        params.append(end_year)
    
    if keyword_field:
        query += " AND LOWER(p.keywords) LIKE ?"
        params.append(f"%{keyword_field}%")

    if selected_fields:
        placeholders = ','.join('?' for _ in selected_fields)
        query += f" AND f.id IN ({placeholders})"
        params.extend(selected_fields)

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return render_template('search_results.html', results=results, keyword=keyword, scope="進階搜尋")


from flask import send_from_directory

@app.route('/secure_pdf/<path:filename>')
def secure_pdf(filename):
    if not session.get('logged_in'):
        flash("請先登入才能瀏覽論文 PDF")
        return redirect(url_for('login'))
    
    return send_from_directory('static/pdf', filename)

    

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import sqlite3

from werkzeug.security import check_password_hash

from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import sqlite3

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        print("🟡 user =", user)
        print("🟡 type(user) =", type(user))
        print("🧩 可用欄位名稱 =", list(user.keys()))

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['role'] = user['role']

            flash(f"✅ 登入成功，歡迎 {user['display_name']}！")

            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))  # 或 user_dashboard

        else:
            flash("❌ 帳號或密碼錯誤，請重新輸入。")

    return render_template('login.html')




@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.* FROM papers p
        JOIN favorites f ON f.paper_id = p.id
        WHERE f.user_id = ?
    """, (user_id,))
    favorites = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', favorites=favorites)


@app.route('/toggle_favorite/<int:paper_id>', methods=['POST'])
def toggle_favorite(paper_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM favorites WHERE user_id = ? AND paper_id = ?", (user_id, paper_id))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM favorites WHERE user_id = ? AND paper_id = ?", (user_id, paper_id))
    else:
        cursor.execute("INSERT OR IGNORE INTO favorites (user_id, paper_id) VALUES (?, ?)", (user_id, paper_id))

    conn.commit()
    conn.close()
    print("✅ 收藏請求來自 user_id =", session.get('user_id'))
    return redirect(url_for('paper_detail', paper_id=paper_id))



@app.route('/about')
def about_professor():
    return render_template('about_professor.html')


@app.route('/admin')

def admin():
    if not session.get('logged_in'):
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/upload-csv', methods=['GET', 'POST'])
def upload_csv():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))

    message = error = None

    if request.method == 'POST':
        import pandas as pd
        import sqlite3

        if 'csv_file' not in request.files:
            error = "❌ 請選擇要上傳的 CSV 檔案。"
            return render_template('upload_csv.html', message=message, error=error)

        file = request.files['csv_file']

        if file.filename == '':
            error = "❌ 檔案名稱為空，請重新上傳。"
            return render_template('upload_csv.html', message=message, error=error)

        if not file.filename.endswith('.csv'):
            error = "❌ 檔案格式錯誤，僅支援 .csv 檔案。"
            return render_template('upload_csv.html', message=message, error=error)

        try:
            df = pd.read_csv(file)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            inserted_papers = 0
            created_fields = set()

            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO papers (title, authors, abstract, source, year, keywords, pdf_filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['title'],
                    row['authors'],
                    row['abstract'],
                    row['source'],
                    row['year'],
                    row['keywords'],
                    row['pdf_filename']
                ))
                paper_id = cursor.lastrowid
                inserted_papers += 1

                # 拆解研究領域（多個以 ; 分隔）
                field_list = [f.strip() for f in str(row['fields']).split(';') if f.strip()]
                for field_name in field_list:
                    cursor.execute("SELECT id FROM fields WHERE name = ?", (field_name,))
                    result = cursor.fetchone()
                    if result:
                        field_id = result[0]
                    else:
                        cursor.execute("INSERT INTO fields (name) VALUES (?)", (field_name,))
                        field_id = cursor.lastrowid
                        created_fields.add(field_name)

                    cursor.execute("INSERT INTO paper_fields (paper_id, field_id) VALUES (?, ?)", (paper_id, field_id))

            conn.commit()
            conn.close()
            message = f"✅ 成功匯入 {inserted_papers} 筆論文資料，建立 {len(created_fields)} 個研究領域。"

        except Exception as e:
            error = f"❌ 匯入失敗：{str(e)}"

    return render_template('upload_csv.html', message=message, error=error)

    
from werkzeug.security import generate_password_hash

@app.route('/upload-pdfs', methods=['GET', 'POST'])
def upload_pdfs():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 僅限管理員使用此功能")
        return redirect(url_for('login'))

    if request.method == 'POST':
        uploaded_files = request.files.getlist('pdf_files')
        success_files = []
        failed_files = []

        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                success_files.append(filename)
            else:
                failed_files.append(file.filename)

        flash(f"✅ 成功上傳 {len(success_files)} 筆 PDF")
        if failed_files:
            flash(f"⚠️ 這些檔案未上傳成功（非 PDF 或檔案異常）：{', '.join(failed_files)}")
        return redirect(url_for('upload_pdfs'))

    return render_template('upload_pdfs.html')


@app.route('/admin/add_user', methods=['GET', 'POST'])
def add_user():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 只有管理員可以新增用戶")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        display_name = request.form['display_name'].strip()
        password = request.form['password']
        role = request.form['role']

        if not username or not password:
            flash("⚠️ 帳號和密碼不可空白")
            return redirect(url_for('add_user'))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), role, display_name)
            )
            conn.commit()
            flash(f"✅ 成功新增用戶 {username}")
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash(f"⚠️ 帳號 {username} 已存在，請換一個")
            return redirect(url_for('add_user'))
        finally:
            conn.close()

    return render_template('add_user.html')

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 只有管理員可以編輯用戶")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 取得該用戶資訊
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("❌ 查無此用戶")
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        display_name = request.form['display_name'].strip()
        role = request.form['role']
        new_password = request.form['password'].strip()

        # 更新資料
        if new_password:
            cursor.execute("""
                UPDATE users SET display_name = ?, role = ?, password_hash = ?
                WHERE id = ?
            """, (display_name, role, generate_password_hash(new_password), user_id))
        else:
            cursor.execute("""
                UPDATE users SET display_name = ?, role = ?
                WHERE id = ?
            """, (display_name, role, user_id))

        conn.commit()
        conn.close()
        flash("✅ 用戶資料已更新")
        return redirect(url_for('admin_users'))

    conn.close()
    return render_template('edit_user.html', user=user)


@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 只有管理員可以刪除用戶")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 不允許刪除admin帳號
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user and user[0] == 'admin':
        flash("⚠️ 管理員帳號不可刪除")
        conn.close()
        return redirect(url_for('admin_users'))

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("✅ 用戶已刪除")
    return redirect(url_for('admin_users'))


@app.route('/admin/users')
def admin_users():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY role DESC, username ASC")
    users = cursor.fetchall()
    conn.close()

    return render_template('admin_users.html', users=users)


@app.route('/admin/papers')
def admin_papers():
    if not session.get('logged_in'):
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 取出所有論文
    cursor.execute("SELECT * FROM papers ORDER BY year DESC")
    papers_raw = cursor.fetchall()

    # 取出每篇論文的所有研究領域（合併處理）
    paper_ids = [p['id'] for p in papers_raw]
    paper_fields = {}
    if paper_ids:
        placeholders = ','.join('?' for _ in paper_ids)
        cursor.execute(f"""
            SELECT pf.paper_id, f.name FROM paper_fields pf
            JOIN fields f ON pf.field_id = f.id
            WHERE pf.paper_id IN ({placeholders})
        """, paper_ids)
        for row in cursor.fetchall():
            paper_fields.setdefault(row['paper_id'], []).append(row['name'])

    # 將研究領域附加到每篇論文資料中
    papers = []
    for p in papers_raw:
        paper = dict(p)
        paper['fields'] = paper_fields.get(p['id'], [])
        papers.append(paper)

    conn.close()
    return render_template('admin_papers_page.html', papers=papers)




@app.route('/add', methods=['GET', 'POST'])
def add_paper():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title'].strip()
        authors = request.form['authors'].strip()
        abstract = request.form['abstract'].strip()
        source = request.form['source'].strip()
        year = request.form['year'].strip()
        keywords = request.form['keywords'].strip()
        field_ids = request.form.getlist('fields')  # 可能是多選
        new_field = request.form.get('new_field', '').strip()
        is_physical = 1 if request.form.get('is_physical') == 'on' else 0
        physical_code = request.form.get('physical_code', '').strip()

        # 若有新研究領域，先新增並取得 id
        if new_field:
            cursor.execute("INSERT OR IGNORE INTO fields (name) VALUES (?)", (new_field,))
            conn.commit()
            cursor.execute("SELECT id FROM fields WHERE name = ?", (new_field,))
            new_id = cursor.fetchone()['id']
            field_ids.append(str(new_id))

        # 儲存 PDF（若有）
        pdf_file = request.files.get('pdf_file')
        pdf_filename = None
        if pdf_file and pdf_file.filename != '' and allowed_file(pdf_file.filename):
            filename = secure_filename(pdf_file.filename)
            pdf_filename = filename
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pdf_file.save(pdf_path)

        # 寫入 papers 資料表
        cursor.execute("""
            INSERT INTO papers (title, authors, abstract, source, year, keywords, pdf_filename, is_physical, physical_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, authors, abstract, source, year, keywords, pdf_filename, is_physical, physical_code))
        paper_id = cursor.lastrowid

        # 寫入 paper_fields 關聯表
        for fid in field_ids:
            cursor.execute("INSERT INTO paper_fields (paper_id, field_id) VALUES (?, ?)", (paper_id, fid))

        conn.commit()
        conn.close()
        flash("✅ 論文新增成功")
        return redirect(url_for('admin_papers'))

    # GET 載入研究領域供選擇
    cursor.execute("SELECT * FROM fields ORDER BY name")
    existing_fields = cursor.fetchall()
    conn.close()
    return render_template('add_paper.html', paper={}, existing_fields=existing_fields)




@app.route('/edit/<int:paper_id>', methods=['GET', 'POST'])
def edit_paper(paper_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 取得論文原始資料（for GET 與 PDF 資訊）
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()
    if not paper:
        conn.close()
        flash("❌ 查無此論文")
        return redirect(url_for('admin_papers'))

    if request.method == 'POST':
        # 取得表單資料
        title = request.form.get('title')
        authors = request.form.get('authors')
        abstract = request.form.get('abstract')
        source = request.form.get('source')
        year = request.form.get('year')
        keywords = request.form.get('keywords')
        is_physical = 1 if request.form.get('is_physical') else 0
        physical_id = request.form.get('physical_id') if is_physical else None
        field_ids = request.form.getlist('fields')
        new_field_name = request.form.get('new_field', '').strip()

        # 若有新增研究領域，先建立
        if new_field_name:
            cursor.execute("INSERT OR IGNORE INTO fields (name) VALUES (?)", (new_field_name,))
            conn.commit()
            cursor.execute("SELECT id FROM fields WHERE name = ?", (new_field_name,))
            new_field_id = cursor.fetchone()['id']
            field_ids.append(str(new_field_id))

        # 清除舊的研究領域關聯，並重建
        cursor.execute("DELETE FROM paper_fields WHERE paper_id = ?", (paper_id,))
        for fid in field_ids:
            cursor.execute("INSERT OR IGNORE INTO paper_fields (paper_id, field_id) VALUES (?, ?)", (paper_id, fid))

        # PDF 處理
        delete_pdf = request.form.get('delete_pdf')
        pdf_file = request.files.get('pdf_file')
        pdf_filename = paper['pdf_filename']  # 預設保留舊檔案

        if delete_pdf and paper['pdf_filename']:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], paper['pdf_filename'])
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            pdf_filename = None

        elif pdf_file and pdf_file.filename != '' and allowed_file(pdf_file.filename):
            filename = secure_filename(pdf_file.filename)
            pdf_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # 刪除舊檔
            if paper['pdf_filename']:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], paper['pdf_filename'])
                if os.path.exists(old_path):
                    os.remove(old_path)
            pdf_filename = filename

        # 更新論文資料
        cursor.execute("""
            UPDATE papers SET 
                title = ?, authors = ?, abstract = ?, source = ?, year = ?, keywords = ?, 
                pdf_filename = ?, is_physical = ?, physical_id = ?
            WHERE id = ?
        """, (title, authors, abstract, source, year, keywords, pdf_filename, is_physical, physical_id, paper_id))

        conn.commit()
        conn.close()
        flash("✅ 論文已成功更新")
        return redirect(url_for('admin_papers'))

    # GET：取得所有欄位與研究領域
    cursor.execute("SELECT * FROM fields ORDER BY name")
    existing_fields = cursor.fetchall()

    cursor.execute("SELECT field_id FROM paper_fields WHERE paper_id = ?", (paper_id,))
    selected_field_ids = [row['field_id'] for row in cursor.fetchall()]

    conn.close()
    return render_template("edit_paper.html", paper=paper,
                           existing_fields=existing_fields,
                           selected_field_ids=selected_field_ids)



@app.route('/delete/<int:paper_id>')
def delete_paper(paper_id):
    if not session.get('logged_in'):
        flash("⚠️ 請以管理員身份登入以進入後台")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 找出舊 PDF
    cursor.execute("SELECT pdf_filename FROM papers WHERE id=?", (paper_id,))
    row = cursor.fetchone()
    if row and row['pdf_filename']:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], row['pdf_filename'])
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    # 刪除資料
    cursor.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_papers'))

@app.route('/admin/fields')
def manage_fields():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fields ORDER BY name")
    fields = cursor.fetchall()

    conn.close()
    return render_template('admin_categories.html', fields=fields)

@app.route('/admin/categories')
def manage_categories():
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash("⚠️ 請以管理員身份登入")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 所有研究領域
    cursor.execute("SELECT * FROM fields ORDER BY name")
    raw_fields = cursor.fetchall()

    # 組裝每個研究領域 + 它的所屬論文 ID
    fields = []
    for field in raw_fields:
        cursor.execute("SELECT paper_id FROM paper_fields WHERE field_id = ?", (field['id'],))
        paper_ids = [row['paper_id'] for row in cursor.fetchall()]
        fields.append({
            'id': field['id'],
            'name': field['name'],
            'paper_ids': paper_ids
        })

    # 所有論文
    cursor.execute("SELECT id, title FROM papers ORDER BY title")
    all_papers = cursor.fetchall()

    conn.close()
    return render_template('admin_categories.html', fields=fields, all_papers=all_papers)



@app.route('/admin/categories/update/<int:field_id>', methods=['POST'])
def update_category(field_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    name = request.form.get('name', '').strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE fields SET name = ? WHERE id = ?", (name, field_id))

    conn.commit()
    conn.close()
    flash("✅ 研究領域名稱已更新")
    return redirect(url_for('manage_categories'))




@app.route('/admin/categories/delete/<int:field_id>')
def delete_category(field_id):
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM paper_fields WHERE field_id = ?", (field_id,))
    cursor.execute("DELETE FROM fields WHERE id = ?", (field_id,))
    conn.commit()
    conn.close()

    flash("🗑 已刪除研究領域")
    return redirect(url_for('manage_categories'))





@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))  # ✅ 改成導回首頁

from email.mime.text import MIMEText
import smtplib
from email.mime.text import MIMEText

@app.route('/paper/<int:paper_id>')
def paper_detail(paper_id):
    if not session.get('logged_in'):
        flash("請先登入才能瀏覽論文詳情")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 取得論文主資料
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()

    if not paper:
        conn.close()
        return "查無此論文", 404

    # 取得研究領域
    cursor.execute("""
        SELECT f.name FROM fields f
        JOIN paper_fields pf ON f.id = pf.field_id
        WHERE pf.paper_id = ?
    """, (paper_id,))
    fields = [row['name'] for row in cursor.fetchall()]

    # ✅ 判斷是否已收藏
    is_favorited = False
    if session.get('user_id'):
        cursor.execute("SELECT 1 FROM favorites WHERE user_id = ? AND paper_id = ?", 
                       (session['user_id'], paper_id))
        is_favorited = cursor.fetchone() is not None

    conn.close()

    return render_template('paper_detail.html', paper=paper, fields=fields, is_favorited=is_favorited)

@app.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        realname = request.form['realname']
        email = request.form['email']
        identity = request.form['identity']
        purpose = request.form['purpose']
        username = request.form['username']
        password = request.form['password']

        # ✉️ Email 內容
        subject = "【館藏系統帳號申請通知】"
        body = f"""
🔔 收到新的帳號申請：

👤 姓名：{realname}
📧 聯絡信箱：{email}
🆔 身分：{identity}
📝 用途：{purpose}

💼 欲申請帳號：{username}
🔐 欲設定密碼：{password}
        """

        sender_email = os.getenv("EMAIL_ADDRESS")
        receiver_email = os.getenv("EMAIL_ADDRESS")
        app_password = os.getenv("EMAIL_PASSWORD")

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = receiver_email

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(msg)

            flash("✅ 申請已提交，管理員將盡快與您聯繫")
        except Exception as e:
            print("❌ 發送失敗：", e)
            flash("❌ 發送失敗，請稍後再試")

        return redirect(url_for('login'))

    return render_template('apply.html')




if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)




