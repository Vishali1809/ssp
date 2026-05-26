import sys

def inject():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    idx = content.find('@app.route(\'/api/chat\', methods=[\'POST\'])')
    if idx == -1:
        print("Could not find api_chat")
        return
    
    new_routes = """
@app.route('/api/rules/html')
def api_rules_html():
    db = get_db()
    q = request.args.get('q', '').strip().lower()
    dept = request.args.get('dept', '').strip()
    year_str = request.args.get('year', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = "SELECT * FROM Corporate_Rules WHERE 1=1"
    params = []

    if q:
        query += " AND (lower(title) LIKE ? OR lower(description_text) LIKE ? OR lower(department) LIKE ? OR lower(category) LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%'])
    if dept:
        query += " AND department = ?"
        params.append(dept)
    if year_str and year_str != '1969':
        try:
            y = int(year_str)
            query += " AND year = ?"
            params.append(y)
        except ValueError:
            pass

    # Count total
    count_query = query.replace("SELECT * FROM Corporate_Rules", "SELECT COUNT(*) FROM Corporate_Rules")
    total = db.execute(count_query, params).fetchone()[0]

    # Pagination
    query += " ORDER BY year DESC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    rules = db.execute(query, params).fetchall()
    
    html = render_template('_rule_cards.html', rules=rules)
    return jsonify({
        "html": html,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })

@app.route('/api/admin/rules/html')
@admin_required
def api_admin_rules_html():
    db = get_db()
    q = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = "SELECT * FROM Corporate_Rules WHERE 1=1"
    params = []

    if q:
        query += " AND (lower(title) LIKE ? OR lower(department) LIKE ? OR lower(category) LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])

    count_query = query.replace("SELECT * FROM Corporate_Rules", "SELECT COUNT(*) FROM Corporate_Rules")
    total = db.execute(count_query, params).fetchone()[0]

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])

    rules = db.execute(query, params).fetchall()
    
    html = render_template('_admin_rule_rows.html', rules=rules)
    return jsonify({
        "html": html,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })

"""
    new_content = content[:idx] + new_routes + content[idx:]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Injected new routes successfully.")

if __name__ == '__main__':
    inject()
