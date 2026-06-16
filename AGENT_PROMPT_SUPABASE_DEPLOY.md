# PANDUAN & AGENT PROMPT — Migrasi ke Supabase + Deploy ke Render

---

## BAGIAN A — YANG HARUS KAMU LAKUKAN SENDIRI (Manual, di Browser)

Agent tidak bisa membuka dashboard web, jadi langkah-langkah ini wajib kamu lakukan sendiri sebelum agent mulai kerja.

### A1. Buat Project Supabase
1. Daftar/login ke https://supabase.com
2. Klik **New Project** → beri nama (misal `akhlak360`) → set password database (simpan baik-baik, ini beda dari password login Supabase kamu)
3. Pilih region terdekat (Singapore biasanya paling dekat untuk Indonesia)
4. Tunggu provisioning selesai (~2 menit)

### A2. Ambil Connection String yang BENAR
1. Di dashboard project, klik tombol **Connect** di bagian atas
2. Pilih tab **Session pooler** (BUKAN "Direct connection" — direct connection cuma IPv6 dan akan gagal connect dari Render nanti)
3. Copy connection string-nya, formatnya seperti ini:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
4. Ganti `[YOUR-PASSWORD]` dengan password yang kamu set di langkah A1
5. **Perhatikan:** username di pooler itu `postgres.xxxxxxxxxxxx` (ada project ref-nya), bukan cuma `postgres` seperti di direct connection. Ini detail yang sering salah ketik.

### A3. Siapkan File `.env` Lokal
Buat file `.env` di root folder `akhlak360/` (sejajar dengan `run.py`), isinya:
```
DATABASE_URL=postgresql://postgres.xxxxxxxxxxxx:password_kamu@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
SECRET_KEY=ganti_dengan_string_random_panjang_apa_saja
FLASK_ENV=development
```
**Jangan commit file ini ke Git.** Nanti agent akan menambahkan `.env` ke `.gitignore`.

### A4. Buat Akun Render (boleh nanti, setelah kode siap)
1. Daftar di https://render.com (bisa pakai akun GitHub)
2. Belum perlu setup apa-apa dulu — tunggu sampai kode sudah jalan lokal dengan Supabase

---

## BAGIAN B — PROMPT UNTUK AGENT (Salin Semua di Bawah Ini)

```
KONTEKS:
Project Flask "akhlak360" ini saat ini menggunakan SQLite sebagai database lokal.
Saya akan deploy ke Render (hosting aplikasi) yang terhubung ke Supabase (PostgreSQL
terkelola) sebagai database production. File .env sudah saya siapkan di root folder
dengan variable DATABASE_URL, SECRET_KEY, dan FLASK_ENV — JANGAN buat ulang isinya,
gunakan apa adanya.

PENTING: Connection ke Supabase HARUS lewat "Session pooler" (sudah ada di .env saya),
JANGAN pernah menyarankan atau mengarah ke "direct connection" (db.xxx.supabase.co)
karena itu IPv6-only dan tidak akan bisa diakses dari Render.

LANGKAH 0 — INSPEKSI DULU (jangan ubah apapun di langkah ini):
1. Baca app/database.py (atau file sejenis yang berisi koneksi database) —
   tunjukkan isinya ke saya dulu
2. Baca semua file migrations/*.sql yang ada
3. Baca requirements.txt
4. Baca run.py dan app/__init__.py untuk melihat bagaimana Flask app object dibuat
   (apakah pakai application factory create_app(), atau langsung app = Flask(__name__))
5. Cari semua file di app/routes/ yang melakukan query database, list nama filenya
Laporkan temuan dari langkah 0 sebelum lanjut ke langkah 1.

LANGKAH 1 — UPDATE requirements.txt
Tambahkan:
  psycopg2-binary
  python-dotenv
  gunicorn
Jangan hapus dependency lain yang sudah ada.

LANGKAH 2 — TULIS ULANG app/database.py UNTUK POSTGRESQL
Ganti seluruh isi sqlite3 dengan psycopg2, tapi JAGA AGAR NAMA FUNGSI dan
SIGNATURE-nya SAMA (get_db(), query_db(query, args, one=False), execute_db(query, args))
supaya semua file route yang sudah memanggil fungsi ini TIDAK PERLU diubah strukturnya.

Gunakan pattern seperti ini sebagai acuan:

    import os
    import psycopg2
    import psycopg2.extras
    from flask import g
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.environ.get("DATABASE_URL")

    def get_db():
        if 'db' not in g:
            g.db = psycopg2.connect(DATABASE_URL, sslmode='require')
        return g.db

    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def query_db(query, args=(), one=False):
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

    def execute_db(query, args=()):
        db = get_db()
        cur = db.cursor()
        cur.execute(query, args)
        db.commit()
        cur.close()

Lalu register close_db ke teardown di app/__init__.py:
    from app.database import close_db
    app.teardown_appcontext(close_db)

LANGKAH 3 — CARI & GANTI PLACEHOLDER SQL DI SEMUA ROUTE FILES
SQLite pakai tanda tanya (?) sebagai placeholder, PostgreSQL/psycopg2 pakai (%s).
Buka SATU PER SATU file di app/routes/ (auth.py, hr.py, employee.py, evaluator.py,
management.py) dan ganti setiap "?" di dalam SQL string menjadi "%s".
JANGAN lakukan find-replace membabi buta di seluruh file — periksa konteksnya,
karena bisa ada tanda tanya yang bukan placeholder SQL (misal di string lain).
Tunjukkan ke saya daftar file yang diubah dan berapa placeholder yang diganti
di masing-masing file.

LANGKAH 4 — KONVERSI MIGRATION SQL KE SYNTAX POSTGRESQL
Buka migrations/001_create_tables.sql (atau file migration yang ada), lalu buat
file baru migrations/001_create_tables_postgres.sql dengan konversi berikut:

| SQLite                          | PostgreSQL                                |
|----------------------------------|--------------------------------------------|
| INTEGER PRIMARY KEY AUTOINCREMENT | INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY |
| DATETIME                         | TIMESTAMP                                  |
| INSERT OR IGNORE INTO            | INSERT INTO ... ON CONFLICT DO NOTHING     |
| INSERT OR REPLACE INTO           | INSERT INTO ... ON CONFLICT (kolom) DO UPDATE SET ... |
| datetime('now')                  | NOW()                                      |

Field lain seperti VARCHAR(n), TEXT, DECIMAL, DATE tetap sama, tidak perlu diubah.
Pertahankan semua FOREIGN KEY constraint apa adanya.

LANGKAH 5 — BUAT SCRIPT MIGRASI YANG BISA DIJALANKAN
Buat file migrations/run_migration.py:

    import os
    import psycopg2
    from dotenv import load_dotenv

    load_dotenv()
    conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
    cur = conn.cursor()
    with open("migrations/001_create_tables_postgres.sql", "r") as f:
        cur.execute(f.read())
    conn.commit()
    print("Migrasi berhasil dijalankan ke Supabase.")
    cur.close()
    conn.close()

Buat juga migrations/run_seed.py dengan pola yang sama, isi datanya dari
seed data roles + indikator AKHLAK + dummy employee yang sudah ada sebelumnya
(lihat file AKHLAK_360_FOUNDATION.fnd bagian SEED DATA).

LANGKAH 6 — SIAPKAN FILE UNTUK DEPLOYMENT
1. Buat file Procfile di root folder:
   web: gunicorn run:app --bind 0.0.0.0:$PORT
   (Sesuaikan "run:app" dengan cara run.py mengekspos object Flask-nya —
   kalau ternyata pakai application factory, sesuaikan jadi
   "run:create_app()" atau buat app = create_app() di level module run.py)
2. Tambahkan/update .gitignore agar berisi minimal:
   .env
   __pycache__/
   *.pyc
   instance/
   *.db
   *.sqlite3
3. Buat file .env.example (TANPA value asli) sebagai dokumentasi:
   DATABASE_URL=
   SECRET_KEY=
   FLASK_ENV=

LANGKAH 7 — TEST LOKAL DULU SEBELUM DEPLOY
1. Jalankan migrations/run_migration.py, laporkan hasilnya
2. Jalankan migrations/run_seed.py, laporkan hasilnya
3. Jalankan python run.py, lalu test: login, CRUD karyawan, submit penilaian
4. Kalau ada error psycopg2 yang muncul, tunjukkan full error message-nya ke saya
   sebelum mencoba memperbaiki sendiri — jangan menebak-nebak fix tanpa konfirmasi

LANGKAH 8 — KONFIRMASI SEBELUM SELESAI
Setelah semua langkah di atas, buat ringkasan singkat:
- File apa saja yang diubah
- File apa saja yang dibuat baru
- Apakah ada bagian dari kode lama (SQLite-specific) yang masih tersisa dan perlu
  saya tinjau manual
JANGAN push ke GitHub atau melakukan apapun di luar folder project ini.
```

---

## BAGIAN C — SETELAH KODE SIAP: DEPLOY KE RENDER (Manual)

Ini juga manual, dilakukan setelah Bagian B selesai dan kamu sudah test lokal berhasil.

1. Push project ke GitHub repository (pastikan `.env` tidak ikut ter-push — cek dengan `git status` dulu)
2. Di Render, klik **New** → **Web Service** → hubungkan ke repo GitHub kamu
3. Isi konfigurasi:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app --bind 0.0.0.0:$PORT`
4. Di bagian **Environment Variables**, tambahkan satu per satu:
   - `DATABASE_URL` → paste connection string Session Pooler dari Supabase (A2)
   - `SECRET_KEY` → string random yang sama/baru
   - `FLASK_ENV` → `production`
5. Klik **Create Web Service**, tunggu build selesai, lalu buka URL yang diberikan Render
6. Test ulang seluruh flow (login per role, submit penilaian, dashboard, generate laporan) di URL production

**Catatan:** Free tier Render akan "tidur" kalau tidak diakses 15 menit, dan butuh ±1 menit untuk bangun di request pertama. Ini normal — kalau dosen kamu mengakses dan loading agak lama di awal, itu bukan bug.

---

## TROUBLESHOOTING UMUM

| Gejala | Kemungkinan Sebab |
|---|---|
| `could not connect to server` di Render | Masih pakai direct connection string, bukan Session Pooler |
| `password authentication failed` | Salah ketik password, atau lupa ganti `[YOUR-PASSWORD]` di connection string |
| `relation "employees" does not exist` | Migration belum dijalankan ke Supabase, jalankan `run_migration.py` |
| Error psycopg2 soal placeholder | Masih ada `?` yang belum diganti `%s` di salah satu file route |
| Berhasil lokal, gagal di Render | Cek environment variables di Render dashboard sudah benar semua |
