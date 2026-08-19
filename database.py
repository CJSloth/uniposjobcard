import sqlite3
import json
import os

DB_FILE = "jobcard.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT UNIQUE NOT NULL,
            contacts TEXT NOT NULL,
            store_email TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_clients_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT NOT NULL,
            reason TEXT NOT NULL,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            requires_sn INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            role TEXT DEFAULT 'Technician',
            assigned_vehicle TEXT,
            primary_min INTEGER NOT NULL,
            primary_max INTEGER NOT NULL,
            current_jc INTEGER NOT NULL,
            secondary_book_min INTEGER,
            secondary_book_max INTEGER,
            authorized_email TEXT,
            pin_code TEXT,
            is_admin INTEGER DEFAULT 0,
            is_primary_dispatch INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_card_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jc_no TEXT UNIQUE NOT NULL,
            tech TEXT NOT NULL,
            client TEXT NOT NULL,
            called_by TEXT,
            vehicle TEXT,
            date_str TEXT NOT NULL,
            fault TEXT,
            actions TEXT,
            items_json TEXT,
            km_driven REAL,
            rate_per_km REAL,
            billable_hrs REAL,
            hourly_rate REAL,
            callout_fee REAL,
            time_start TEXT,
            time_end TEXT,
            customer_comments TEXT,
            payment_method TEXT,
            subtotal REAL NOT NULL,
            vat REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Completed',
            client_signature TEXT,
            tech_signature TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tech_name TEXT NOT NULL,
            book_min INTEGER NOT NULL,
            book_max INTEGER NOT NULL,
            jobs_json TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    run_migrations()

migration_cols = [
    ("role", "TEXT DEFAULT 'Technician'"),
    ("km_driven", "REAL"),
    ("rate_per_km", "REAL"),
    ("billable_hrs", "REAL"),
    ("hourly_rate", "REAL"),
    ("callout_fee", "REAL"),
    ("time_start", "TEXT"),
    ("time_end", "TEXT"),
    ("customer_comments", "TEXT"),
    ("payment_method", "TEXT"),
    ("authorized_email", "TEXT"),
    ("pin_code", "TEXT"),
    ("is_admin", "INTEGER DEFAULT 0"),
    ("is_primary_dispatch", "INTEGER DEFAULT 0"),
    ("secondary_book_min", "INTEGER"),
    ("secondary_book_max", "INTEGER"),
    ("store_email", "TEXT"),
    ("franchise_group", "TEXT"),
    ("client_signature", "TEXT"),
    ("tech_signature", "TEXT")
]

def run_migrations():
    conn = get_connection()
    cursor = conn.cursor()
    for col_name, col_type in migration_cols:
        try:
            cursor.execute(f"ALTER TABLE job_card_history ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass
        try:
            cursor.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_type}")
        except Exception:
            pass

    conn.commit()
    conn.close()
    seed_initial_data()

def seed_initial_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO vehicles (reg_no) VALUES (?)", [("HLB897FS",), ("BFN999FS",), ("NANCY",)])

    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        default_clients = [
            ("Cat Box Pet Hyper Garsfontein", json.dumps(["Dan", "Dave", "Jason", "Sarah"]), "garsfontein@catbox.co.za"),
            ("Cat Box Pet Hyper Centurion", json.dumps(["Mike", "Johan"]), "centurion@catbox.co.za"),
            ("Cat Box Pet Hyper Rayton", json.dumps(["Anita", "Coenraad"]), "rayton@catbox.co.za"),
            ("Oasis Braamfontein", json.dumps(["Sipho", "Tebogo"]), "braamfontein@oasis.co.za"),
            ("GoZone Water Mead", json.dumps(["Mead", "Johan"]), "mead@gozone.co.za")
        ]
        cursor.executemany("INSERT INTO clients (store_name, contacts, store_email) VALUES (?, ?, ?)", default_clients)

    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        default_items = [
            ("Unipos POS Server Terminal", 12500.00, 1, "Hardware / Terminals"),
            ("22 Inch LCD Monitor", 1850.00, 1, "Monitors & Displays"),
            ("Honeywell Barcode Scanner", 1450.00, 1, "Scanners & Peripherals"),
            ("USB Keyboard & Mouse Combo", 350.00, 0, "Accessories & Cables"),
            ("Branch Management Installation Fee", 2500.00, 0, "Services & Installs"),
            ("TJ Installation & Config", 1800.00, 0, "Services & Installs"),
            ("General Store Servicing", 950.00, 0, "Services & Installs")
        ]
        cursor.executemany("INSERT INTO inventory (item_name, price, requires_sn, category) VALUES (?, ?, ?, ?)", default_items)

    cursor.execute("SELECT COUNT(*) FROM technicians")
    if cursor.fetchone()[0] == 0:
        default_techs = [
            ("C.J. Celliers", "Both", "HLB897FS", 1000, 1999, 1042, 5000, 5099, "c.j.celliers2002@gmail.com", "1234", 1, 1),
            ("William", "Technician", "BFN999FS", 2000, 2999, 2015, None, None, "williamkrause@gmail.com", "1111", 0, 0)
        ]
        cursor.executemany('''
            INSERT INTO technicians 
            (name, role, assigned_vehicle, primary_min, primary_max, current_jc, secondary_book_min, secondary_book_max, authorized_email, pin_code, is_admin, is_primary_dispatch) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_techs)

    conn.commit()
    conn.close()

def get_all_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT store_name, contacts, store_email, franchise_group FROM clients")
    rows = cursor.fetchall()
    conn.close()
    return {
        row["store_name"]: {
            "contacts": json.loads(row["contacts"]),
            "email": row["store_email"] or "",
            "franchise_group": row["franchise_group"] or "Independent / Ungrouped"
        } for row in rows
    }

def update_client_franchise(store_name, franchise_group):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clients SET franchise_group = ? WHERE store_name = ?", (franchise_group.strip(), store_name))
    conn.commit()
    conn.close()

def add_client_contact(store_name, new_contact):
    clients = get_all_clients()
    if store_name in clients:
        contacts_list = clients[store_name]["contacts"]
        if new_contact not in contacts_list:
            contacts_list.append(new_contact)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE clients SET contacts = ? WHERE store_name = ?", (json.dumps(contacts_list), store_name))
            conn.commit()
            conn.close()

def update_store_email_list(store_name, email_list):
    if not email_list:
        return
    all_emails_str = ", ".join(email_list)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clients SET store_email = ? WHERE store_name = ?", (all_emails_str, store_name))
    conn.commit()
    conn.close()

def get_inventory_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, price, requires_sn, category FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    return {
        row["item_name"]: {
            "price": row["price"],
            "requires_sn": bool(row["requires_sn"]),
            "category": row["category"]
        } for row in rows
    }

def get_vehicles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT reg_no FROM vehicles")
    rows = cursor.fetchall()
    conn.close()
    return [row["reg_no"] for row in rows]

def get_technicians_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM technicians")
    rows = cursor.fetchall()
    conn.close()
    return {
        row["name"]: {
            "role": row["role"] or ('Admin' if row["is_admin"] else 'Technician'),
            "assigned_vehicle": row["assigned_vehicle"],
            "primary_min": row["primary_min"],
            "primary_max": row["primary_max"],
            "current_jc": row["current_jc"],
            "secondary_book_min": row["secondary_book_min"],
            "secondary_book_max": row["secondary_book_max"],
            "authorized_email": row["authorized_email"] or "",
            "pin_code": row["pin_code"] or "",
            "is_admin": bool(row["is_admin"]),
            "is_primary_dispatch": bool(row["is_primary_dispatch"])
        } for row in rows
    }

def save_job_card(record):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO job_card_history 
        (jc_no, tech, client, called_by, vehicle, date_str, fault, actions, items_json,
         km_driven, rate_per_km, billable_hrs, hourly_rate, callout_fee, time_start, time_end, customer_comments, payment_method,
         subtotal, vat, total, client_signature, tech_signature)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record.get("jc_no"),
        record.get("tech"),
        record.get("client"),
        record.get("called_by"),
        record.get("vehicle"),
        record.get("date"),
        record.get("fault"),
        record.get("actions"),
        json.dumps(record.get("items", [])),
        record.get("km_driven"),
        record.get("rate_per_km"),
        record.get("billable_hrs"),
        record.get("hourly_rate"),
        record.get("callout_fee"),
        record.get("time_start"),
        record.get("time_end"),
        record.get("customer_comments"),
        record.get("payment_method"),
        record.get("subtotal"),
        record.get("vat"),
        record.get("total"),
        record.get("client_signature"),
        record.get("tech_signature")
    ))

    tech_name = record.get("tech")
    if tech_name:
        cursor.execute("UPDATE technicians SET current_jc = current_jc + 1 WHERE name = ?", (tech_name,))

    conn.commit()
    conn.close()

def get_job_card_history(tech_filter=None):
    conn = get_connection()
    cursor = conn.cursor()
    if tech_filter:
        cursor.execute("SELECT * FROM job_card_history WHERE tech = ? ORDER BY id DESC", (tech_filter,))
    else:
        cursor.execute("SELECT * FROM job_card_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def archive_completed_book(tech_name, book_min, book_max):
    all_jobs = get_job_card_history(tech_filter=tech_name)
    book_jobs = []
    for j in all_jobs:
        jc_str = j['jc_no'].replace('JC-', '')
        if jc_str.isdigit():
            num = int(jc_str)
            if book_min <= num <= book_max:
                book_jobs.append(j)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO completed_books (tech_name, book_min, book_max, jobs_json)
        VALUES (?, ?, ?, ?)
    ''', (tech_name, book_min, book_max, json.dumps(book_jobs)))
    conn.commit()
    conn.close()

def get_completed_books(tech_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, book_min, book_max, jobs_json FROM completed_books WHERE tech_name = ? ORDER BY id DESC", (tech_name,))
    rows = cursor.fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r["id"]] = {
            "min": r["book_min"],
            "max": r["book_max"],
            "jobs": json.loads(r["jobs_json"])
        }
    return result

init_db()