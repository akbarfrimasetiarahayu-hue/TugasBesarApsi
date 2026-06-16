import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

def hash_password(plain_text: str) -> str:
    return bcrypt.hashpw(plain_text.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

load_dotenv()
conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
cur = conn.cursor()

try:
    print("  -> Seeding roles...")
    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] == 0:
        roles = [
            ('hr', 'Human Resource Administrator'),
            ('karyawan', 'Karyawan biasa'),
            ('evaluator', 'Penilai (atasan/rekan/bawahan)'),
            ('management', 'Manajemen/Top Management'),
        ]
        cur.executemany("INSERT INTO roles (role_name, description) VALUES (%s, %s)", roles)

    print("  -> Seeding indikator AKHLAK...")
    cur.execute("SELECT COUNT(*) FROM indikators")
    if cur.fetchone()[0] == 0:
        indikators = [
            (1, 'Menyelesaikan tugas sesuai komitmen dan tepat waktu', 1, 5),
            (1, 'Bertanggung jawab atas hasil kerja', 1, 5),
            (1, 'Jujur dalam melaporkan pekerjaan', 1, 5),
            (2, 'Memiliki pengetahuan dan keterampilan yang dibutuhkan', 1, 5),
            (2, 'Terus belajar dan meningkatkan kompetensi', 1, 5),
            (2, 'Menghasilkan pekerjaan berkualitas tinggi', 1, 5),
            (3, 'Menghargai perbedaan dan keberagaman', 1, 5),
            (3, 'Menciptakan suasana kerja yang kondusif', 1, 5),
            (3, 'Membantu rekan kerja yang membutuhkan', 1, 5),
            (4, 'Mendahulukan kepentingan bangsa dan negara', 1, 5),
            (4, 'Menjaga nama baik perusahaan', 1, 5),
            (4, 'Patuh pada kebijakan dan regulasi perusahaan', 1, 5),
            (5, 'Cepat menyesuaikan diri dengan perubahan', 1, 5),
            (5, 'Berinovasi dalam pekerjaan', 1, 5),
            (5, 'Proaktif menghadapi tantangan baru', 1, 5),
            (6, 'Bekerja sama lintas divisi/tim secara efektif', 1, 5),
            (6, 'Aktif berkontribusi dalam kerja tim', 1, 5),
            (6, 'Terbuka menerima masukan dari rekan kerja', 1, 5),
        ]
        cur.executemany("INSERT INTO indikators (core_value, indikator_name, nilai_min, nilai_max) VALUES (%s, %s, %s, %s)", indikators)

    print("  -> Seeding karyawan dummy...")
    cur.execute("SELECT COUNT(*) FROM employees")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id",
            ('Budi Santoso', 'budi.santoso@energinusantara.co.id', 'EN-001', 'Direktur Utama', 'Direksi', None)
        )
        direktur_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id",
            ('Siti Rahayu', 'siti.rahayu@energinusantara.co.id', 'EN-002', 'Manager HR', 'Human Resource', direktur_id)
        )
        manager_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (%s, %s, %s, %s, %s, %s)",
            ('Ahmad Fauzi', 'ahmad.fauzi@energinusantara.co.id', 'EN-003', 'Staff Operasional', 'Operasional', manager_id)
        )
        cur.execute(
            "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (%s, %s, %s, %s, %s, %s)",
            ('Dewi Lestari', 'dewi.lestari@energinusantara.co.id', 'EN-004', 'Staff Keuangan', 'Keuangan', manager_id)
        )
        cur.execute(
            "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (%s, %s, %s, %s, %s, %s)",
            ('Rizky Pratama', 'rizky.pratama@energinusantara.co.id', 'EN-005', 'Staff IT', 'IT', manager_id)
        )

    print("  -> Seeding user accounts...")
    cur.execute("SELECT id_role, role_name FROM roles")
    roles_map = {r[1]: r[0] for r in cur.fetchall()}

    cur.execute("SELECT user_id, nip FROM employees")
    employees_map = {e[1]: e[0] for e in cur.fetchall()}

    if employees_map:
        accounts = [
            (employees_map.get('EN-002'), roles_map.get('hr'),         'hr.admin',     'Admin@123'),
            (employees_map.get('EN-003'), roles_map.get('karyawan'),   'ahmad.fauzi',  'Karyawan@123'),
            (employees_map.get('EN-001'), roles_map.get('evaluator'),  'budi.direksi', 'Evaluator@123'),
            (employees_map.get('EN-001'), roles_map.get('management'), 'management',   'Mgmt@123'),
        ]
        
        cur.execute("SELECT COUNT(*) FROM user_accounts")
        if cur.fetchone()[0] == 0:
            for id_emp, id_role, username, password_plain in accounts:
                if id_emp and id_role:
                    hashed = hash_password(password_plain)
                    cur.execute(
                        "INSERT INTO user_accounts (id_employee, id_role, username, password, status) VALUES (%s, %s, %s, %s, 'active')",
                        (id_emp, id_role, username, hashed)
                    )

    print("  -> Seeding periode penilaian...")
    cur.execute("SELECT COUNT(*) FROM assessment_periods")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO assessment_periods (period_name, start_date, end_date, status) VALUES (%s, %s, %s, %s)",
            ('Semester 1 2026', '2026-01-01', '2026-06-30', 'active')
        )

    conn.commit()
    print("[OK] Seed data berhasil dijalankan ke Supabase.")
except Exception as e:
    conn.rollback()
    print(f"[ERROR] Error saat seed: {e}")
finally:
    cur.close()
    conn.close()
