import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def init_db():
    if os.path.exists(DATABASE):
        try:
            os.remove(DATABASE)
            print("Removed existing database.db for fresh initialization.")
        except Exception as e:
            print(f"Warning: Could not remove database.db: {e}")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # ── Users Table ──────────────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        username   TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        role       TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
        department TEXT NOT NULL,
        full_name  TEXT DEFAULT ''
    )
    ''')

    # ── Corporate Rules Table ────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Corporate_Rules (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        title            TEXT NOT NULL,
        category         TEXT NOT NULL,
        year             INTEGER NOT NULL CHECK(year >= 1970 AND year <= 2030),
        department       TEXT NOT NULL,
        description_text TEXT NOT NULL,
        file_path        TEXT,
        summary          TEXT,
        ocr_text         TEXT,
        view_count       INTEGER DEFAULT 0,
        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ── Announcements Table ──────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Announcements (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT NOT NULL,
        content    TEXT NOT NULL,
        is_active  INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ── Activity Log Table ───────────────────────────────────────────────────
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Activity_Log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        action     TEXT NOT NULL,
        details    TEXT,
        username   TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ── Seed Users ───────────────────────────────────────────────────────────
    users = [
        ('ssp_admin',      generate_password_hash('admin123'),  'admin',    'Management',  'HR Administrator'),
        ('hr_admin',       generate_password_hash('admin123'),  'admin',    'HR',          'HR Manager'),
        ('employee1',      generate_password_hash('emp123'),    'employee', 'HR',          'Rajesh Kumar'),
        ('safety_worker',  generate_password_hash('user123'),   'employee', 'Safety',      'Murugan S'),
        ('prod_staff',     generate_password_hash('user123'),   'employee', 'Production',  'Senthil R'),
    ]
    for username, pw, role, dept, full_name in users:
        cursor.execute(
            'INSERT INTO Users (username, password, role, department, full_name) VALUES (?,?,?,?,?)',
            (username, pw, role, dept, full_name)
        )
        print(f"  Created user: {username} [{role}] — {dept}")

    # ── Seed Corporate Rules ─────────────────────────────────────────────────
    rules = [
        (
            "Annual Leave & Casual Leave Entitlement Policy",
            "Leave Management",
            2024,
            "HR",
            "All permanent employees of Salem Steel Plant are entitled to 30 days of Earned Leave, 8 days of Casual Leave, and 4 days of Special Casual Leave per calendar year as per SAIL corporate guidelines. Leave encashment is permitted for up to 50% of accumulated Earned Leave at the time of superannuation.",
            "Employees earn 30 days annual leave, 8 casual leave, and 4 special casual leave per year. Up to 50% of Earned Leave can be encashed on retirement."
        ),
        (
            "Personal Protective Equipment (PPE) Compliance Directive",
            "Safety & Compliance",
            2023,
            "Safety",
            "All shop-floor personnel, contractors, and visitors entering operational zones of Salem Steel Plant must mandatorily wear approved PPE including hard hats, safety boots (IS 15298 certified), high-visibility vests, safety glasses, and hearing protection in high-noise zones exceeding 85 dB. Non-compliance will result in immediate suspension from the plant premises.",
            "Mandatory PPE required in all operational zones. Includes hard hats, safety boots, HV vests, safety glasses, and hearing protection above 85 dB."
        ),
        (
            "Medical Benefits and Healthcare Scheme — SAIL Employees",
            "Medical & Benefits",
            2022,
            "HR",
            "SAIL Salem Steel Plant provides comprehensive medical coverage under the SAIL Medical Benefit Scheme (MBS) to all regular employees and their dependents (spouse, two children, and dependent parents). The scheme covers OPD, hospitalization, specialized treatment, and critical illness up to the limits prescribed in the SAIL Medical Policy 2022. Employees may access the Plant Hospital and empanelled hospitals across Tamil Nadu.",
            "SAIL Medical Benefit Scheme covers employees and dependents (spouse, 2 children, parents) for OPD, hospitalization, and critical illness under SAIL Medical Policy 2022."
        ),
        (
            "Environmental Emission Standards and Green Compliance Protocol",
            "Environmental",
            2021,
            "Safety",
            "Salem Steel Plant commits to maintaining ambient air quality within CPCB-prescribed norms. All blast furnace, coke oven, and rolling mill operations must install and maintain real-time emission monitoring systems. Monthly environmental audit reports must be submitted to the State Pollution Control Board. Violations will attract penalties under the Environment Protection Act, 1986.",
            "All plant operations must comply with CPCB emission norms. Real-time monitoring mandatory. Monthly audit reports submitted to State Pollution Control Board."
        ),
        (
            "Performance Appraisal and Promotion Guidelines",
            "Career Development",
            2023,
            "Management",
            "Annual Performance Appraisal for all officers (E1–E9 grades) is conducted from January to March. Appraisal scores are mapped to a five-point rating scale. Promotions are recommendation-based and require a minimum of 3 years in the current grade, a performance rating of 3.5 or above averaged over three consecutive years, and departmental vacancy availability. Moderation committees review all appraisals before finalization.",
            "Annual appraisals conducted Jan-Mar for E1-E9 grades. Promotions require 3 years in grade, 3.5+ average rating over 3 years, and vacancy availability."
        ),
        (
            "Attendance and Punctuality Regulations — Shop Floor",
            "Attendance",
            2020,
            "Production",
            "Shop floor employees must mark biometric attendance at the designated entry gates. Tardiness exceeding 10 minutes per shift shall be treated as half-day leave. Habitual late-coming (more than 4 instances in a calendar month) will be referred to the respective department head for disciplinary action. Attendance records are maintained in the HRMS portal and are accessible to employees.",
            "Biometric attendance mandatory. Tardiness over 10 minutes counts as half-day leave. Over 4 late marks per month triggers disciplinary review."
        ),
        (
            "Foundry Operational Shift Directives",
            "Operations",
            1974,
            "Production",
            "Establishment of standard 8-hour shift rotations and mandatory break periods for all blast furnace operatives to ensure maximum efficiency and workforce health. Three shifts: Morning (6AM–2PM), Afternoon (2PM–10PM), Night (10PM–6AM). Overtime is permissible only with supervisor written approval.",
            "8-hour shift rotations established for all blast furnace operatives. Three shifts: Morning, Afternoon, Night. Overtime requires written supervisor approval."
        ),
        (
            "IT Systems and Data Security Policy",
            "IT & Security",
            2025,
            "Management",
            "All SAIL Salem Steel Plant computer systems and network infrastructure are for official use only. Employees must not install unauthorized software, access personal social media during working hours on plant systems, or share login credentials. All data must be stored on designated servers. Cybersecurity incidents must be reported to the IT helpdesk within 1 hour of discovery. Password reset is mandatory every 90 days.",
            "Plant IT systems are for official use only. No unauthorized software or social media. Report security incidents within 1 hour. Password reset every 90 days."
        ),
    ]

    for title, category, year, dept, desc, summary in rules:
        cursor.execute('''
            INSERT INTO Corporate_Rules (title, category, year, department, description_text, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, category, year, dept, desc, summary))
        print(f"  Seeded rule: '{title}' [{year} — {dept}]")

    # ── Seed Announcements ───────────────────────────────────────────────────
    announcements = [
        (
            "SAIL Annual Sports Meet — Registrations Open",
            "All Salem Steel Plant employees are invited to register for the Annual Sports Meet 2026 to be held on 15-Jun-2026. Events include cricket, badminton, carrom, and athletics. Register via HRMS portal by 31-May-2026."
        ),
        (
            "Mandatory Fire Safety Refresher Training — May 2026",
            "All production and safety department employees must attend the mandatory Fire Safety Refresher Training scheduled for 28-May-2026 and 29-May-2026. Attendance is compulsory. Contact the Safety Department for your batch allocation."
        ),
        (
            "HRMS Portal Upgrade — Scheduled Downtime Notice",
            "The HRMS portal will undergo scheduled maintenance and upgrade on 26-May-2026 from 10:00 PM to 6:00 AM. Services including leave applications and attendance view will be unavailable during this period."
        ),
    ]
    for title, content in announcements:
        cursor.execute(
            'INSERT INTO Announcements (title, content) VALUES (?, ?)',
            (title, content)
        )
        print(f"  Seeded announcement: '{title}'")

    conn.commit()
    conn.close()
    print("\n[OK] Database initialized and seeded successfully.")
    print("   Admin login:    ssp_admin / admin123")
    print("   Employee login: employee1 / emp123")
    print("   Employee login: safety_worker / user123")

if __name__ == '__main__':
    init_db()
