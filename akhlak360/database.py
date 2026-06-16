"""
database.py — Helper koneksi SQLite
Sistem Penilaian 360° Core Values AKHLAK
"""

import sqlite3
import os
from config import config


def get_db():
    """Membuat dan mengembalikan koneksi database SQLite."""
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row  # Agar hasil query bisa diakses seperti dict
    conn.execute("PRAGMA foreign_keys = ON")  # Aktifkan foreign key enforcement
    return conn


def init_db():
    """Inisialisasi database: jalankan migrasi SQL."""
    migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '001_create_tables.sql')
    conn = get_db()
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print("✅ Database berhasil diinisialisasi.")


def query_db(query, args=(), one=False):
    """Helper untuk query SELECT."""
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    """Helper untuk INSERT / UPDATE / DELETE, kembalikan lastrowid."""
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id
