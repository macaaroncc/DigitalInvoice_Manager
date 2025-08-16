import sqlite3
import os

DB_NAME = "invoices.db"

def init_db():
    """Crea la base de datos y la tabla si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Crear tabla principal si no existe
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            date TEXT NOT NULL,
            folder TEXT NOT NULL,
            status TEXT DEFAULT 'incompleto'
        )
    """)
    
    # Verificar si la columna 'name' existe, si no, añadirla
    try:
        cur.execute("SELECT name FROM invoices LIMIT 1")
    except sqlite3.OperationalError:
        # La columna no existe, añadirla
        print("Añadiendo columna 'name' a la base de datos...")
        cur.execute("ALTER TABLE invoices ADD COLUMN name TEXT DEFAULT ''")
        print("Columna 'name' añadida exitosamente.")
    
    conn.commit()
    conn.close()


def add_invoice(number, name, date, folder, status="incompleto"):
    """Añade una factura a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO invoices (number, name, date, folder, status)
        VALUES (?, ?, ?, ?, ?)
    """, (number, name, date, folder, status))
    conn.commit()
    conn.close()


def get_invoices():
    """Obtiene todas las facturas de la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices ORDER BY date DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_invoice_status(number, status):
    """Actualiza el estado de una factura."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET status=? WHERE number=?", (status, number))
    conn.commit()
    conn.close()

def update_invoice_name(number, name):
    """Actualiza el nombre de una factura."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET name=? WHERE number=?", (name, number))
    conn.commit()
    conn.close()

def delete_invoice(number):
    import sqlite3
    conn = sqlite3.connect("invoices.db")
    c = conn.cursor()
    c.execute("DELETE FROM invoices WHERE number = ?", (number,))
    conn.commit()
    conn.close()
