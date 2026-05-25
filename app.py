import os
import sqlite3
import json
import io
import requests
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory, g, jsonify)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

# ── Optional heavy imports (graceful degradation) ────────────────────────────
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import pytesseract
    from PIL import Image
    # Update this path if Tesseract is installed elsewhere on Windows
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_SUPPORT = True
except ImportError:
    OCR_SUPPORT = False

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

# ── App Configuration ────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'ssp_hr_portal_ultra_secure_secret_2026_salem_steel'

DATABASE      = 'database.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'png', 'jpg', 'jpeg'}
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyA3bvJrFRAREFhWwjvSLsEGPC5R30QCbJg')
GEMINI_URL     = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── Database Helpers ─────────────────────────────────────────────────────────
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def log_activity(action, details='', username=None):
    try:
        db = get_db()
        db.execute(
            'INSERT INTO Activity_Log (action, details, username) VALUES (?,?,?)',
            (action, details, username or session.get('username', 'system'))
        )
        db.commit()
    except Exception:
        pass


# ── Jinja2 Custom Filters ────────────────────────────────────────────────────
@app.template_filter('ddmmyyyy')
def format_date(value):
    """Convert SQLite timestamp or date string to DD-MM-YYYY."""
    if not value:
        return '—'
    try:
        if isinstance(value, str):
            dt = datetime.strptime(value[:10], '%Y-%m-%d')
        else:
            dt = value
        return dt.strftime('%d-%m-%Y')
    except Exception:
        return str(value)

@app.template_filter('truncate_words')
def truncate_words(s, num=20):
    words = str(s).split()
    if len(words) <= num:
        return s
    return ' '.join(words[:num]) + '…'


# ── Utility Helpers ──────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    if not PDF_SUPPORT:
        return ''
    try:
        reader = PyPDF2.PdfReader(filepath)
        text = ''
        for i in range(min(5, len(reader.pages))):
            text += (reader.pages[i].extract_text() or '') + '\n'
        return text.strip()
    except Exception:
        return ''

def extract_text_from_image(filepath):
    if not OCR_SUPPORT:
        return ''
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='eng')
        return text.strip()
    except Exception:
        return ''

def extract_text_from_docx(filepath):
    if not DOCX_SUPPORT:
        return ''
    try:
        doc = docx.Document(filepath)
        return '\n'.join([p.text for p in doc.paragraphs]).strip()
    except Exception:
        return ''

def extract_document_text(filepath, filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ('png', 'jpg', 'jpeg'):
        return extract_text_from_image(filepath)
    elif ext in ('docx', 'doc'):
        return extract_text_from_docx(filepath)
    return ''

def call_gemini(prompt):
    """Call Gemini 1.5 Flash API server-side. Returns text or None."""
    if not GEMINI_API_KEY:
        return None
    try:
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"Gemini API failure: status_code={resp.status_code}, response={resp.text}", flush=True)
    except Exception as e:
        print(f"Gemini API exception error: {e}", flush=True)
    return None

def generate_summary(text):
    """Generate 2–3 sentence summary via Gemini."""
    if not text:
        return None
    prompt = (
        "You are an HR assistant for Salem Steel Plant, India. "
        "Summarize the following HR policy or rule document in exactly 2-3 clear, "
        "simple sentences suitable for a plant employee to read quickly. "
        "Be direct and factual:\n\n" + text[:5000]
    )
    return call_gemini(prompt)


# ── Auth Decorators ──────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════════════════════
#  PUBLIC ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    db = get_db()
    # Latest 6 rules for homepage preview
    latest_rules = db.execute(
        "SELECT * FROM Corporate_Rules ORDER BY created_at DESC LIMIT 6"
    ).fetchall()
    # Active announcements
    announcements = db.execute(
        "SELECT * FROM Announcements WHERE is_active=1 ORDER BY created_at DESC"
    ).fetchall()
    # Stats
    total_rules = db.execute("SELECT COUNT(*) FROM Corporate_Rules").fetchone()[0]
    total_dept  = db.execute("SELECT COUNT(DISTINCT department) FROM Corporate_Rules").fetchone()[0]
    year_range  = db.execute("SELECT MIN(year), MAX(year) FROM Corporate_Rules").fetchone()
    return render_template(
        'index.html',
        latest_rules=latest_rules,
        announcements=announcements,
        total_rules=total_rules,
        total_dept=total_dept,
        year_from=year_range[0] or 1970,
        year_to=year_range[1] or 2026,
    )


# ── Login / Logout ────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        db = get_db()
        user = db.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            if user['role'] != 'admin':
                flash('Access denied. This portal is for administrators only.', 'danger')
                return render_template('login.html')

            session['user_id']    = user['id']
            session['username']   = user['username']
            session['full_name']  = user['full_name']
            session['role']       = user['role']
            session['department'] = user['department']

            log_activity('LOGIN', f"Admin {username} logged in", username)
            flash(f"Welcome back, {user['full_name'] or username}!", 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    username = session.get('username', '')
    log_activity('LOGOUT', f"User {username} logged out", username)
    session.clear()
    flash('You have been securely logged out.', 'success')
    return redirect(url_for('index'))


# ── Public Rule Search API ────────────────────────────────────────────────────
@app.route('/api/rules')
def api_rules():
    db = get_db()
    rules = db.execute(
        "SELECT id, title, summary, description_text, department, category, year FROM Corporate_Rules"
    ).fetchall()
    return jsonify({"rules": [dict(r) for r in rules]})

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify({"suggestions": []})
    db = get_db()
    rows = db.execute(
        """SELECT DISTINCT title FROM Corporate_Rules
           WHERE lower(title) LIKE ? OR lower(category) LIKE ? OR lower(department) LIKE ?
           LIMIT 6""",
        (f'%{q}%', f'%{q}%', f'%{q}%')
    ).fetchall()
    return jsonify({"suggestions": [r['title'] for r in rows]})

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json(silent=True) or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Load rules as context
    db = get_db()
    rules = db.execute(
        "SELECT title, summary, description_text FROM Corporate_Rules LIMIT 20"
    ).fetchall()
    context = '\n\n'.join(
        f"Rule: {r['title']}\nSummary: {r['summary'] or ''}\nDetails: {r['description_text']}"
        for r in rules
    )

    prompt = (
        "You are an HR assistant for Salem Steel Plant (SAIL). "
        "Use the following HR rules and policies as context to answer the employee's question. "
        "Be concise, professional, and helpful. Answer in 2-4 sentences.\n\n"
        f"HR RULES CONTEXT:\n{context}\n\n"
        f"EMPLOYEE QUESTION: {question}\n\nANSWER:"
    )

    answer = call_gemini(prompt)
    if answer:
        return jsonify({"answer": answer})
    elif not GEMINI_API_KEY:
        return jsonify({"answer": (
            "The AI assistant is not configured. Please set the GEMINI_API_KEY "
            "environment variable to enable AI-powered responses."
        )})
    else:
        return jsonify({"answer": "I'm sorry, I was unable to process your request at this time. Please try again."}), 500


# ── File Download ─────────────────────────────────────────────────────────────
@app.route('/download/<int:rule_id>')
def download(rule_id):
    db = get_db()
    rule = db.execute("SELECT * FROM Corporate_Rules WHERE id=?", (rule_id,)).fetchone()
    if not rule or not rule['file_path']:
        flash('Document not found.', 'danger')
        return redirect(url_for('index'))
    # Increment view count
    db.execute("UPDATE Corporate_Rules SET view_count = view_count + 1 WHERE id=?", (rule_id,))
    db.commit()
    return send_from_directory(
        os.path.abspath(app.config['UPLOAD_FOLDER']),
        rule['file_path'],
        as_attachment=False
    )


# ════════════════════════════════════════════════════════════════════════════
#  EMPLOYEE ROUTES (read-only)
# ════════════════════════════════════════════════════════════════════════════

@app.route('/employee/dashboard')
def employee_dashboard():
    db = get_db()
    dept_filter = request.args.get('dept', '')
    if dept_filter:
        rules = db.execute(
            "SELECT * FROM Corporate_Rules WHERE department=? ORDER BY year DESC",
            (dept_filter,)
        ).fetchall()
    else:
        rules = db.execute(
            "SELECT * FROM Corporate_Rules ORDER BY year DESC"
        ).fetchall()
    departments = db.execute(
        "SELECT DISTINCT department FROM Corporate_Rules ORDER BY department"
    ).fetchall()
    return render_template(
        'employee_dashboard.html',
        rules=rules,
        departments=departments,
        active_dept=dept_filter,
    )


# ════════════════════════════════════════════════════════════════════════════
#  ADMIN ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    rules = db.execute(
        "SELECT * FROM Corporate_Rules ORDER BY created_at DESC"
    ).fetchall()
    # Dashboard stats
    total_rules   = db.execute("SELECT COUNT(*) FROM Corporate_Rules").fetchone()[0]
    total_users   = db.execute("SELECT COUNT(*) FROM Users WHERE role='employee'").fetchone()[0]
    total_dept    = db.execute("SELECT COUNT(DISTINCT department) FROM Corporate_Rules").fetchone()[0]
    recent_month  = db.execute(
        "SELECT COUNT(*) FROM Corporate_Rules WHERE created_at >= date('now','-30 days')"
    ).fetchone()[0]
    recent_activity = db.execute(
        "SELECT * FROM Activity_Log ORDER BY created_at DESC LIMIT 8"
    ).fetchall()
    top_viewed = db.execute(
        "SELECT * FROM Corporate_Rules ORDER BY view_count DESC LIMIT 5"
    ).fetchall()
    departments = db.execute(
        "SELECT DISTINCT department FROM Corporate_Rules ORDER BY department"
    ).fetchall()
    return render_template(
        'admin_dashboard.html',
        rules=rules,
        total_rules=total_rules,
        total_users=total_users,
        total_dept=total_dept,
        recent_month=recent_month,
        recent_activity=recent_activity,
        top_viewed=top_viewed,
        departments=departments,
        active_section='dashboard',
    )


@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_rule():
    title       = request.form.get('title', '').strip()
    category    = request.form.get('category', '').strip()
    year_str    = request.form.get('year', '').strip()
    department  = request.form.get('department', '').strip()
    description = request.form.get('description', '').strip()

    if not all([title, category, year_str, department, description]):
        flash('All required fields must be filled.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        year = int(year_str)
        if year < 1970 or year > 2030:
            raise ValueError()
    except ValueError:
        flash('Invalid year. Must be between 1970 and 2030.', 'danger')
        return redirect(url_for('admin_dashboard'))

    file_path = None
    summary   = None
    ocr_text  = None

    file = request.files.get('file')
    if file and file.filename:
        if allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            ts        = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_fn = f"{ts}_{department.lower()}_{year}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_fn)
            file.save(save_path)
            file_path = unique_fn

            # Extract text for OCR/AI
            extracted = extract_document_text(save_path, filename)
            if extracted:
                ocr_text = extracted
                summary  = generate_summary(extracted)
            elif description:
                summary = generate_summary(description)
        else:
            flash('Unsupported file format. Use PDF, DOCX, TXT, PNG, JPG.', 'danger')
            return redirect(url_for('admin_dashboard'))
    else:
        # Generate summary from description text
        summary = generate_summary(description)

    db = get_db()
    db.execute(
        '''INSERT INTO Corporate_Rules
           (title, category, year, department, description_text, file_path, summary, ocr_text)
           VALUES (?,?,?,?,?,?,?,?)''',
        (title, category, year, department, description, file_path, summary, ocr_text)
    )
    db.commit()
    log_activity('RULE_CREATED', f"Rule '{title}' created for {department} [{year}]")
    flash(f"Rule '{title}' published successfully." + (' AI summary generated.' if summary else ''), 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit/<int:rule_id>', methods=['POST'])
@admin_required
def edit_rule(rule_id):
    title       = request.form.get('title', '').strip()
    category    = request.form.get('category', '').strip()
    year_str    = request.form.get('year', '').strip()
    department  = request.form.get('department', '').strip()
    description = request.form.get('description', '').strip()

    try:
        year = int(year_str)
        if year < 1970 or year > 2030:
            raise ValueError()
    except ValueError:
        flash('Invalid year.', 'danger')
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    file = request.files.get('file')
    now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if file and file.filename:
        if allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            ts        = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_fn = f"{ts}_{department.lower()}_{year}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_fn)
            file.save(save_path)

            extracted = extract_document_text(save_path, filename)
            summary   = generate_summary(extracted or description) if (extracted or description) else None
            ocr_text  = extracted

            db.execute(
                '''UPDATE Corporate_Rules
                   SET title=?, category=?, year=?, department=?, description_text=?,
                       file_path=?, summary=?, ocr_text=?, updated_at=?
                   WHERE id=?''',
                (title, category, year, department, description, unique_fn, summary, ocr_text, now, rule_id)
            )
        else:
            flash('Unsupported file format.', 'danger')
            return redirect(url_for('admin_dashboard'))
    else:
        db.execute(
            '''UPDATE Corporate_Rules
               SET title=?, category=?, year=?, department=?, description_text=?, updated_at=?
               WHERE id=?''',
            (title, category, year, department, description, now, rule_id)
        )

    db.commit()
    log_activity('RULE_UPDATED', f"Rule ID {rule_id} updated")
    flash('Rule updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete/<int:rule_id>', methods=['POST'])
@admin_required
def delete_rule(rule_id):
    db = get_db()
    rule = db.execute("SELECT * FROM Corporate_Rules WHERE id=?", (rule_id,)).fetchone()
    if rule:
        if rule['file_path']:
            fp = os.path.join(app.config['UPLOAD_FOLDER'], rule['file_path'])
            if os.path.exists(fp):
                os.remove(fp)
        db.execute("DELETE FROM Corporate_Rules WHERE id=?", (rule_id,))
        db.commit()
        log_activity('RULE_DELETED', f"Rule '{rule['title']}' deleted")
        flash(f"Rule '{rule['title']}' deleted successfully.", 'success')
    return redirect(url_for('admin_dashboard'))


# ── Admin Analytics ───────────────────────────────────────────────────────────
@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    db = get_db()

    # Rules by department
    dept_stats = db.execute(
        "SELECT department, COUNT(*) as count FROM Corporate_Rules GROUP BY department ORDER BY count DESC"
    ).fetchall()

    # Rules by year (last 10 years)
    year_stats = db.execute(
        "SELECT year, COUNT(*) as count FROM Corporate_Rules GROUP BY year ORDER BY year DESC LIMIT 15"
    ).fetchall()

    # Rules by category
    cat_stats = db.execute(
        "SELECT category, COUNT(*) as count FROM Corporate_Rules GROUP BY category ORDER BY count DESC LIMIT 8"
    ).fetchall()

    # Most viewed
    top_viewed = db.execute(
        "SELECT * FROM Corporate_Rules ORDER BY view_count DESC LIMIT 8"
    ).fetchall()

    # Recent uploads (last 30 days)
    recent = db.execute(
        "SELECT * FROM Corporate_Rules ORDER BY created_at DESC LIMIT 10"
    ).fetchall()

    # Activity log
    activity = db.execute(
        "SELECT * FROM Activity_Log ORDER BY created_at DESC LIMIT 15"
    ).fetchall()

    total_rules  = db.execute("SELECT COUNT(*) FROM Corporate_Rules").fetchone()[0]
    total_views  = db.execute("SELECT SUM(view_count) FROM Corporate_Rules").fetchone()[0] or 0
    with_files   = db.execute("SELECT COUNT(*) FROM Corporate_Rules WHERE file_path IS NOT NULL").fetchone()[0]
    with_summary = db.execute("SELECT COUNT(*) FROM Corporate_Rules WHERE summary IS NOT NULL").fetchone()[0]

    return render_template(
        'admin_analytics.html',
        dept_stats=dept_stats,
        year_stats=year_stats,
        cat_stats=cat_stats,
        top_viewed=top_viewed,
        recent=recent,
        activity=activity,
        total_rules=total_rules,
        total_views=total_views,
        with_files=with_files,
        with_summary=with_summary,
        active_section='analytics',
    )


# ── Admin OCR Scanner ─────────────────────────────────────────────────────────
@app.route('/admin/ocr', methods=['GET', 'POST'])
@admin_required
def admin_ocr():
    extracted_text = None
    filename_used  = None
    error_msg      = None

    if request.method == 'POST':
        file = request.files.get('ocr_file')
        if file and file.filename:
            if allowed_file(file.filename):
                filename  = secure_filename(file.filename)
                ts        = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_fn = f"ocr_{ts}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_fn)
                file.save(save_path)
                filename_used = filename

                ext = filename.rsplit('.', 1)[1].lower()
                if ext in ('png', 'jpg', 'jpeg') and OCR_SUPPORT:
                    extracted_text = extract_text_from_image(save_path)
                elif ext == 'pdf' and PDF_SUPPORT:
                    extracted_text = extract_text_from_pdf(save_path)
                    if not extracted_text and OCR_SUPPORT:
                        # Try image-based OCR on PDF (scanned PDF)
                        extracted_text = "[Scanned PDF — text layer not found. Please convert to image for OCR.]"
                elif ext in ('docx', 'doc') and DOCX_SUPPORT:
                    extracted_text = extract_text_from_docx(save_path)
                else:
                    if not OCR_SUPPORT and ext in ('png', 'jpg', 'jpeg'):
                        error_msg = "OCR support not available. Please install pytesseract and Pillow."
                    elif not PDF_SUPPORT and ext == 'pdf':
                        error_msg = "PDF support not available. Please install PyPDF2."
                    else:
                        error_msg = "Unable to extract text from this file type."

                # Clean up temp file if not useful
                if not extracted_text and not error_msg:
                    extracted_text = "[No text could be extracted from this document.]"
            else:
                error_msg = "Unsupported file format. Use PNG, JPG, PDF, or DOCX."
        else:
            error_msg = "Please select a file to scan."

    return render_template(
        'admin_ocr.html',
        extracted_text=extracted_text,
        filename_used=filename_used,
        error_msg=error_msg,
        ocr_support=OCR_SUPPORT,
        active_section='ocr',
    )


# ── Admin Announcements ───────────────────────────────────────────────────────
@app.route('/admin/announcements', methods=['GET', 'POST'])
@admin_required
def admin_announcements():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            title   = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            if title and content:
                db.execute('INSERT INTO Announcements (title, content) VALUES (?,?)', (title, content))
                db.commit()
                flash('Announcement added.', 'success')
        elif action == 'delete':
            ann_id = request.form.get('ann_id')
            db.execute('DELETE FROM Announcements WHERE id=?', (ann_id,))
            db.commit()
            flash('Announcement deleted.', 'success')
        elif action == 'toggle':
            ann_id = request.form.get('ann_id')
            db.execute('UPDATE Announcements SET is_active = 1 - is_active WHERE id=?', (ann_id,))
            db.commit()
            flash('Announcement status updated.', 'success')
        return redirect(url_for('admin_announcements'))

    announcements = db.execute('SELECT * FROM Announcements ORDER BY created_at DESC').fetchall()
    return render_template(
        'admin_dashboard.html',
        announcements=announcements,
        active_section='announcements',
        rules=db.execute("SELECT * FROM Corporate_Rules ORDER BY created_at DESC").fetchall(),
        total_rules=db.execute("SELECT COUNT(*) FROM Corporate_Rules").fetchone()[0],
        total_users=db.execute("SELECT COUNT(*) FROM Users WHERE role='employee'").fetchone()[0],
        total_dept=db.execute("SELECT COUNT(DISTINCT department) FROM Corporate_Rules").fetchone()[0],
        recent_month=db.execute(
            "SELECT COUNT(*) FROM Corporate_Rules WHERE created_at >= date('now','-30 days')"
        ).fetchone()[0],
        recent_activity=db.execute("SELECT * FROM Activity_Log ORDER BY created_at DESC LIMIT 8").fetchall(),
        top_viewed=db.execute("SELECT * FROM Corporate_Rules ORDER BY view_count DESC LIMIT 5").fetchall(),
        departments=db.execute("SELECT DISTINCT department FROM Corporate_Rules ORDER BY department").fetchall(),
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
