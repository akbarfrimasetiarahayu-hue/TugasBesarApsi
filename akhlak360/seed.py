"""
seed.py — Seed data awal untuk database AKHLAK 360°
Berisi: roles, 18 indikator AKHLAK, 5 karyawan dummy, 1 akun per role
Jalankan: python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from database import get_db, init_db


def hash_password(plain_text: str) -> str:
    """Hash password dengan bcrypt."""
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def seed_roles(conn):
    """Seed data roles."""
    print("  → Seeding roles...")
    roles = [
        ('hr', 'Human Resource Administrator'),
        ('karyawan', 'Karyawan biasa'),
        ('evaluator', 'Penilai (atasan/rekan/bawahan)'),
        ('management', 'Manajemen/Top Management'),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO roles (role_name, description) VALUES (?, ?)",
        roles
    )


def seed_indikators(conn):
    """Seed 18 indikator AKHLAK (3 per core value)."""
    print("  → Seeding indikator AKHLAK...")
    indikators = [
        # Amanah (core_value=1)
        (1, 'Menyelesaikan tugas sesuai komitmen dan tepat waktu', 1, 5),
        (1, 'Bertanggung jawab atas hasil kerja', 1, 5),
        (1, 'Jujur dalam melaporkan pekerjaan', 1, 5),
        # Kompeten (core_value=2)
        (2, 'Memiliki pengetahuan dan keterampilan yang dibutuhkan', 1, 5),
        (2, 'Terus belajar dan meningkatkan kompetensi', 1, 5),
        (2, 'Menghasilkan pekerjaan berkualitas tinggi', 1, 5),
        # Harmonis (core_value=3)
        (3, 'Menghargai perbedaan dan keberagaman', 1, 5),
        (3, 'Menciptakan suasana kerja yang kondusif', 1, 5),
        (3, 'Membantu rekan kerja yang membutuhkan', 1, 5),
        # Loyal (core_value=4)
        (4, 'Mendahulukan kepentingan bangsa dan negara', 1, 5),
        (4, 'Menjaga nama baik perusahaan', 1, 5),
        (4, 'Patuh pada kebijakan dan regulasi perusahaan', 1, 5),
        # Adaptif (core_value=5)
        (5, 'Cepat menyesuaikan diri dengan perubahan', 1, 5),
        (5, 'Berinovasi dalam pekerjaan', 1, 5),
        (5, 'Proaktif menghadapi tantangan baru', 1, 5),
        # Kolaboratif (core_value=6)
        (6, 'Bekerja sama lintas divisi/tim secara efektif', 1, 5),
        (6, 'Aktif berkontribusi dalam kerja tim', 1, 5),
        (6, 'Terbuka menerima masukan dari rekan kerja', 1, 5),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO indikators (core_value, indikator_name, nilai_min, nilai_max) VALUES (?, ?, ?, ?)",
        indikators
    )


def seed_employees(conn):
    """Seed 5 karyawan dummy dengan struktur organisasi."""
    print("  → Seeding karyawan dummy...")

    # Struktur: Direktur → Manager → 3 Staff
    # employee 1: Direktur (Management) — no supervisor
    # employee 2: Manager HR — supervisor: Direktur
    # employee 3: Karyawan Operasional — supervisor: Manager HR
    # employee 4: Karyawan Keuangan — supervisor: Manager HR
    # employee 5: Karyawan IT — supervisor: Manager HR

    # Cek apakah sudah ada data
    existing = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    if existing > 0:
        print("  → Data karyawan sudah ada, skip.")
        return

    # Masukkan tanpa supervisor dulu
    conn.execute(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        ('Budi Santoso', 'budi.santoso@energinusantara.co.id', 'EN-001', 'Direktur Utama', 'Direksi', None)
    )
    direktur_id = conn.execute("SELECT user_id FROM employees WHERE nip='EN-001'").fetchone()[0]

    conn.execute(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        ('Siti Rahayu', 'siti.rahayu@energinusantara.co.id', 'EN-002', 'Manager HR', 'Human Resource', direktur_id)
    )
    manager_id = conn.execute("SELECT user_id FROM employees WHERE nip='EN-002'").fetchone()[0]

    conn.execute(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        ('Ahmad Fauzi', 'ahmad.fauzi@energinusantara.co.id', 'EN-003', 'Staff Operasional', 'Operasional', manager_id)
    )
    conn.execute(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        ('Dewi Lestari', 'dewi.lestari@energinusantara.co.id', 'EN-004', 'Staff Keuangan', 'Keuangan', manager_id)
    )
    conn.execute(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        ('Rizky Pratama', 'rizky.pratama@energinusantara.co.id', 'EN-005', 'Staff IT', 'IT', manager_id)
    )
    print("  → 5 karyawan berhasil dibuat.")


def seed_user_accounts(conn):
    """Seed akun login: 1 per role + 1 untuk karyawan tambahan."""
    print("  → Seeding user accounts...")

    # Ambil ID role
    roles = {r['role_name']: r['id_role'] for r in conn.execute("SELECT id_role, role_name FROM roles").fetchall()}

    # Ambil ID karyawan
    employees = {e['nip']: e['user_id'] for e in conn.execute("SELECT user_id, nip FROM employees").fetchall()}

    if not employees:
        print("  ⚠ Tidak ada karyawan, skip user accounts.")
        return

    accounts = [
        # (id_employee, id_role, username, password_plain)
        (employees.get('EN-002'), roles.get('hr'),         'hr.admin',     'Admin@123'),     # HR = Manager HR
        (employees.get('EN-003'), roles.get('karyawan'),   'ahmad.fauzi',  'Karyawan@123'),  # Karyawan
        (employees.get('EN-001'), roles.get('evaluator'),  'budi.direksi', 'Evaluator@123'), # Evaluator = Direktur
        (employees.get('EN-001'), roles.get('management'), 'management',   'Mgmt@123'),      # Management = Direktur
    ]

    existing_accounts = conn.execute("SELECT COUNT(*) FROM user_accounts").fetchone()[0]
    if existing_accounts > 0:
        print("  → Akun sudah ada, skip.")
        return

    for id_emp, id_role, username, password_plain in accounts:
        if id_emp and id_role:
            hashed = hash_password(password_plain)
            conn.execute(
                "INSERT OR IGNORE INTO user_accounts (id_employee, id_role, username, password, status) VALUES (?, ?, ?, ?, 'active')",
                (id_emp, id_role, username, hashed)
            )

    print("  → Akun berhasil dibuat:")
    print("     • HR       : username=hr.admin       | password=Admin@123")
    print("     • Karyawan : username=ahmad.fauzi    | password=Karyawan@123")
    print("     • Evaluator: username=budi.direksi   | password=Evaluator@123")
    print("     • Management: username=management    | password=Mgmt@123")


def seed_period(conn):
    """Seed satu periode penilaian aktif sebagai contoh."""
    existing = conn.execute("SELECT COUNT(*) FROM assessment_periods").fetchone()[0]
    if existing > 0:
        return
    print("  → Seeding periode penilaian...")
    conn.execute(
        "INSERT INTO assessment_periods (period_name, start_date, end_date, status) VALUES (?, ?, ?, ?)",
        ('Semester 1 2026', '2026-01-01', '2026-06-30', 'active')
    )


def run_seed():
    """Jalankan semua seed data."""
    print("\nMemulai proses seed database AKHLAK 360...")

    # Inisialisasi database (jalankan migrasi)
    init_db()

    conn = get_db()
    try:
        seed_roles(conn)
        seed_indikators(conn)
        seed_employees(conn)
        seed_user_accounts(conn)
        seed_period(conn)
        conn.commit()
        print("\n✅ Seed data berhasil! Database siap digunakan.\n")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error saat seed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    run_seed()
