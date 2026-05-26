import re
import sys

def modify_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "import json" not in content:
        content = content.replace("import os", "import os\nimport json")

    # 1. Update upload_rule
    upload_start = content.find("@app.route('/admin/upload', methods=['POST'])")
    upload_end = content.find("@app.route('/admin/edit/<int:rule_id>', methods=['POST'])")
    
    if upload_start == -1 or upload_end == -1:
        print("Could not find upload_rule")
        return
        
    new_upload = """@app.route('/admin/upload', methods=['POST'])
@admin_required
def upload_rule():
    title       = request.form.get('title', '').strip()
    category    = request.form.get('category', '').strip()
    year_str    = request.form.get('year', '').strip()
    department  = request.form.get('department', '').strip()
    description = request.form.get('description', '').strip()
    files       = request.files.getlist('files')

    has_files = any(f and f.filename for f in files)

    if not all([title, category, year_str, department]) or (not description and not has_files):
        flash('All required fields must be filled (Title, Category, Year, Department, and either a Description or a File).', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        year = int(year_str)
        if year < 1970 or year > 2030:
            raise ValueError()
    except ValueError:
        flash('Invalid year. Must be between 1970 and 2030.', 'danger')
        return redirect(url_for('admin_dashboard'))

    saved_files = []
    combined_ocr = []
    
    for file in files:
        if file and file.filename:
            if allowed_file(file.filename):
                filename  = secure_filename(file.filename)
                ts        = datetime.now().strftime('%Y%m%d%H%M%S')
                unique_fn = f"{ts}_{department.lower()}_{year}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_fn)
                file.save(save_path)
                saved_files.append(unique_fn)

                extracted = extract_document_text(save_path, filename)
                if extracted:
                    combined_ocr.append(extracted)
            else:
                flash(f'Unsupported file format: {file.filename}', 'danger')
                return redirect(url_for('admin_dashboard'))

    file_path = json.dumps(saved_files) if saved_files else None
    ocr_text = "\\n\\n".join(combined_ocr) if combined_ocr else None
    
    if ocr_text:
        summary = generate_summary(ocr_text)
    elif description:
        summary = generate_summary(description)
    else:
        summary = None

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

"""
    content = content[:upload_start] + new_upload + content[upload_end:]
    
    # 2. Update edit_rule
    edit_start = content.find("@app.route('/admin/edit/<int:rule_id>', methods=['POST'])")
    edit_end = content.find("@app.route('/admin/delete/<int:rule_id>', methods=['POST'])")
    
    new_edit = """@app.route('/admin/edit/<int:rule_id>', methods=['POST'])
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
    files = request.files.getlist('files')
    now  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    has_files = any(f and f.filename for f in files)

    if has_files:
        saved_files = []
        combined_ocr = []
        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    filename  = secure_filename(file.filename)
                    ts        = datetime.now().strftime('%Y%m%d%H%M%S')
                    unique_fn = f"{ts}_{department.lower()}_{year}_{filename}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_fn)
                    file.save(save_path)
                    saved_files.append(unique_fn)

                    extracted = extract_document_text(save_path, filename)
                    if extracted:
                        combined_ocr.append(extracted)
                else:
                    flash(f'Unsupported file format: {file.filename}', 'danger')
                    return redirect(url_for('admin_dashboard'))

        file_path = json.dumps(saved_files)
        ocr_text = "\\n\\n".join(combined_ocr) if combined_ocr else None
        summary = generate_summary(ocr_text or description) if (ocr_text or description) else None

        db.execute(
            '''UPDATE Corporate_Rules
               SET title=?, category=?, year=?, department=?, description_text=?,
                   file_path=?, summary=?, ocr_text=?, updated_at=?
               WHERE id=?''',
            (title, category, year, department, description, file_path, summary, ocr_text, now, rule_id)
        )
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

"""
    content = content[:edit_start] + new_edit + content[edit_end:]
    
    # 3. Update delete_rule
    delete_start = content.find("@app.route('/admin/delete/<int:rule_id>', methods=['POST'])")
    delete_end = content.find("# ── Admin Analytics ───────────────────────────────────────────────────────────")
    
    new_delete = """@app.route('/admin/delete/<int:rule_id>', methods=['POST'])
@admin_required
def delete_rule(rule_id):
    db = get_db()
    rule = db.execute("SELECT * FROM Corporate_Rules WHERE id=?", (rule_id,)).fetchone()
    if rule:
        if rule['file_path']:
            try:
                files = json.loads(rule['file_path'])
            except:
                files = [rule['file_path']]
            
            for f_path in files:
                fp = os.path.join(app.config['UPLOAD_FOLDER'], f_path)
                if os.path.exists(fp):
                    os.remove(fp)
        db.execute("DELETE FROM Corporate_Rules WHERE id=?", (rule_id,))
        db.commit()
        log_activity('RULE_DELETED', f"Rule '{rule['title']}' deleted")
        flash(f"Rule '{rule['title']}' deleted successfully.", 'success')
    return redirect(url_for('admin_dashboard'))

"""
    content = content[:delete_start] + new_delete + content[delete_end:]
    
    # 4. Update download rule
    download_start = content.find("@app.route('/download/<int:rule_id>')")
    download_end = content.find("# ════════════════════════════════════════════════════════════════════════════\n#  EMPLOYEE ROUTES")
    
    new_download = """import zipfile
import io

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
    
    try:
        files = json.loads(rule['file_path'])
    except:
        files = [rule['file_path']]

    if len(files) == 1:
        return send_from_directory(
            os.path.abspath(app.config['UPLOAD_FOLDER']),
            files[0],
            as_attachment=False
        )
    else:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for f in files:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                if os.path.exists(file_path):
                    # add file to zip, taking only the actual original filename or keeping the unique name
                    zf.write(file_path, os.path.basename(f))
        memory_file.seek(0)
        return send_file(memory_file, download_name=f"Rule_{rule_id}_documents.zip", as_attachment=True)

"""
    content = content[:download_start] + new_download + content[download_end:]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
        print("Updated app.py successfully")

modify_app()
