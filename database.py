import sqlite3
import json
import os

DB_FILE = "jobcard.db"

def get_connection():
    """Connects to the SQLite database file (creates it if it doesn't exist)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initializes the database schema for inventory, clients, technicians, and history."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Clients & Contacts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT UNIQUE NOT NULL,
            contacts TEXT NOT NULL
        )
    ''')

    # 2. Fleet Vehicles Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL
        )
    ''')

    # 3. Inventory & Pricing Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            requires_sn INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    ''')

    # 4. Technicians & Ranges Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            assigned_vehicle TEXT,
            primary_min INTEGER NOT NULL,
            primary_max INTEGER NOT NULL,
            current_jc INTEGER NOT NULL,
            secondary_book_min INTEGER,
            secondary_book_max INTEGER
        )
    ''')

    # 5. Completed & Saved Job Cards History Table
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
            status TEXT DEFAULT 'Completed'
        )
    ''')

    # Safe Schema Migrations for existing database files
    migration_cols = [
        ("km_driven", "REAL"),
        ("rate_per_km", "REAL"),
        ("billable_hrs", "REAL"),
        ("hourly_rate", "REAL"),
        ("callout_fee", "REAL"),
        ("time_start", "TEXT"),
        ("time_end", "TEXT"),
        ("customer_comments", "TEXT"),
        ("payment_method", "TEXT")
    ]
    for col_name, col_type in migration_cols:
        try:
            cursor.execute(f"ALTER TABLE job_card_history ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
    
    seed_initial_data()

def seed_initial_data():
    """Seeds default Unipos data if tables are brand new."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vehicles")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO vehicles (reg_no) VALUES (?)", [("HLB897FS",), ("BFN999FS",)])

    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        default_clients = [
            ("Cat Box Pet Hyper Garsfontein", json.dumps(["Dan", "Dave", "Jason", "Sarah"])),
            ("Cat Box Pet Hyper Centurion", json.dumps(["Mike", "Johan"])),
            ("Cat Box Pet Hyper Rayton", json.dumps(["Anita", "Coenraad"])),
            ("Oasis Braamfontein", json.dumps(["Sipho", "Tebogo"])),
            ("GoZone Water Mead", json.dumps(["Mead", "Johan"]))
        ]
        cursor.executemany("INSERT INTO clients (store_name, contacts) VALUES (?, ?)", default_clients)

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
            ("C.J. Celliers", "HLB897FS", 1000, 1999, 1042, 5000, 5099),
            ("William", "BFN999FS", 2000, 2999, 2015, None, None),
            ("Mr. Mark", "HLB897FS", 3000, 3999, 3008, None, None)
        ]
        cursor.executemany('''
            INSERT INTO technicians 
            (name, assigned_vehicle, primary_min, primary_max, current_jc, secondary_book_min, secondary_book_max) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_techs)

    conn.commit()
    conn.close()

def get_all_clients():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT store_name, contacts FROM clients")
    rows = cursor.fetchall()
    conn.close()
    return {row["store_name"]: json.loads(row["contacts"]) for row in rows}

def add_client_contact(store_name, new_contact):
    clients = get_all_clients()
    if store_name in clients:
        if new_contact not in clients[store_name]:
            clients[store_name].append(new_contact)
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE clients SET contacts = ? WHERE store_name = ?", (json.dumps(clients[store_name]), store_name))
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
            "assigned_vehicle": row["assigned_vehicle"],
            "primary_min": row["primary_min"],
            "primary_max": row["primary_max"],
            "current_jc": row["current_jc"],
            "secondary_book_min": row["secondary_book_min"],
            "secondary_book_max": row["secondary_book_max"]
        } for row in rows
    }

def save_job_card(record):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO job_card_history 
        (jc_no, tech, client, called_by, vehicle, date_str, fault, actions, items_json,
         km_driven, rate_per_km, billable_hrs, hourly_rate, callout_fee, time_start, time_end, customer_comments, payment_method,
         subtotal, vat, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        record.get("km_driven", 0.0),
        record.get("rate_per_km", 7.50),
        record.get("billable_hrs", 1.0),
        record.get("hourly_rate", 650.0),
        record.get("callout_fee", 450.0),
        record.get("time_start", ""),
        record.get("time_end", ""),
        record.get("customer_comments", ""),
        record.get("payment_method", ""),
        record.get("subtotal", 0.0),
        record.get("vat", 0.0),
        record.get("total", 0.0)
    ))

    # Auto-increment JC counter
    tech_name = record.get("tech")
    if tech_name:
        cursor.execute("UPDATE technicians SET current_jc = current_jc + 1 WHERE name = ?", (tech_name,))

    conn.commit()
    conn.close()

def get_job_card_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_card_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

init_db()