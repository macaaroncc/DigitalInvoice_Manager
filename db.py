import sqlite3
import os

DB_NAME = "invoices.db"

def init_db():
    """Crea la base de datos y la tabla si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            date TEXT NOT NULL,
            folder TEXT NOT NULL,
            status TEXT DEFAULT 'incompleto'
        )
    """)
    conn.commit()
    conn.close()


def add_invoice(number, date, folder, status="incompleto"):
    """Añade una factura a la base de datos."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO invoices (number, date, folder, status)
        VALUES (?, ?, ?, ?)
    """, (number, date, folder, status))
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

def delete_invoice(number):
    import sqlite3
    conn = sqlite3.connect("invoices.db")
    c = conn.cursor()
    c.execute("DELETE FROM invoices WHERE number = ?", (number,))
    conn.commit()
    conn.close()
