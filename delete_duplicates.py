import sqlite3

def delete_duplicates():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Let's find rules with the title 'Annual'
    c.execute("SELECT id, title, description_text FROM Corporate_Rules WHERE title = 'Annual'")
    rows = c.fetchall()
    print("Found 'Annual' rows:", len(rows))
    
    if len(rows) > 1:
        # Keep the first one (min id), delete the rest
        min_id = rows[0][0]
        for r in rows:
            if r[0] < min_id:
                min_id = r[0]
                
        # Delete all others
        ids_to_delete = [r[0] for r in rows if r[0] != min_id]
        
        for i in ids_to_delete:
            c.execute("DELETE FROM Corporate_Rules WHERE id = ?", (i,))
        
        conn.commit()
        print(f"Deleted {len(ids_to_delete)} duplicate 'Annual' rules.")
    else:
        print("No duplicates found for 'Annual'.")
        
delete_duplicates()
