import sqlite3
import os

DB_NAME = "invoices.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        number TEXT,
                        client TEXT,
                        date TEXT,
                        items TEXT,
                        folder TEXT
                      )''')
    conn.commit()
    conn.close()

def add_invoice(number, client, date, items, folder):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invoices (number, client, date, items, folder) VALUES (?, ?, ?, ?, ?)",
                   (number, client, date, items, folder))
    conn.commit()
    conn.close()

def get_invoices():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, client, date, folder FROM invoices ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
