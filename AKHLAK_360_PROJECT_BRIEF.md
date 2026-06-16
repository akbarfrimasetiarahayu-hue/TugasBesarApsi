# AKHLAK 360° Assessment System — Project Brief
> Tugas IS Project 2026 | Kelompok FRI-086 | Kelas TI-47-08  
> Advisor: HILMAN DWI ANGGANA, S.Si., M.Si.

---

## Ringkasan Proyek

Kamu diminta membangun **Sistem Penilaian 360° Core Values AKHLAK** berbasis web untuk PT. Energi Nusantara (perusahaan BUMN sektor energi). Sistem ini mengukur internalisasi nilai **Amanah, Kompeten, Harmonis, Loyal, Adaptif, Kolaboratif** pada karyawan melalui penilaian dari berbagai perspektif.

---

## Teknologi yang Digunakan

- **Framework:** Antigravity (wajib sesuai instruksi dosen)
- **Frontend:** HTML + CSS + JavaScript (atau sesuai Antigravity stack)
- **Database:** Relasional (MySQL / SQLite) — lihat skema di `AKHLAK_360_FOUNDATION.fnd`
- **Bahasa:** Indonesia (UI), dengan komentar kode dalam Bahasa Indonesia atau Inggris

---

## Role Pengguna (4 Role)

| Role | Akses Utama |
|---|---|
| **HR Admin** | Kelola karyawan, atur periode penilaian, assign evaluator, lihat semua hasil, generate laporan |
| **Karyawan** | Self-assessment, lihat hasil evaluasi diri sendiri, lihat rekomendasi IDP |
| **Evaluator** (Atasan/Rekan/Bawahan) | Isi form penilaian AKHLAK untuk karyawan yang ditugaskan |
| **Management** | Dashboard read-only, view analytics, generate & export laporan |

---

## Halaman yang Harus Dibuat

### Semua Role
- [ ] `login.html` — Login dengan email + password, redirect ke dashboard sesuai role
- [ ] `logout` — Konfirmasi logout, clear session

### HR Admin
- [ ] `hr/dashboard.html` — Overview: total karyawan, progress penilaian, grafik ringkasan
- [ ] `hr/employees.html` — CRUD data karyawan (tambah, edit, hapus, lihat)
- [ ] `hr/periods.html` — Buat & kelola periode penilaian (nama, tanggal mulai, tanggal selesai)
- [ ] `hr/assign.html` — Assign evaluator ke karyawan (atasan, rekan, bawahan otomatis dari struktur org)
- [ ] `hr/results.html` — Lihat hasil penilaian semua karyawan
- [ ] `hr/reports.html` — Generate & download laporan (PDF / Excel)

### Karyawan
- [ ] `employee/dashboard.html` — Status penilaian, notifikasi pending
- [ ] `employee/self-assessment.html` — Form pengisian self-assessment berbasis indikator AKHLAK
- [ ] `employee/my-results.html` — Lihat skor akhir + gap analysis + rekomendasi IDP

### Evaluator
- [ ] `evaluator/dashboard.html` — Daftar karyawan yang perlu dinilai
- [ ] `evaluator/assess.html` — Form penilaian AKHLAK untuk karyawan tertentu (skor + feedback)

### Management
- [ ] `management/dashboard.html` — Grafik penilaian, progress evaluasi, statistik per divisi
- [ ] `management/performance.html` — Performance review: rekomendasi, skor, feedback
- [ ] `management/reports.html` — Generate & export laporan

---

## Fitur Wajib

### Fungsional
1. **Manajemen Data Karyawan** — CRUD oleh HR
2. **Pengaturan Periode Penilaian** — HR set tanggal mulai & selesai
3. **Auto-Assign Evaluator** — Berdasarkan struktur organisasi (id_supervisor)
4. **Form Penilaian AKHLAK** — 6 nilai × beberapa indikator per nilai, dengan skala skor
5. **Self-Assessment** — Karyawan menilai diri sendiri
6. **Perhitungan Nilai Otomatis** dengan bobot:
   - Atasan: **40%**
   - Bawahan: **30%**
   - Rekan Kerja: **20%**
   - Diri Sendiri: **10%**
7. **Gap Analysis** — Tampilkan perbedaan penilaian antar evaluator (chart/tabel)
8. **Dashboard Interaktif** — Grafik skor, progress, statistik
9. **Notifikasi & Reminder** — Otomatis ke pengguna yang belum selesai menilai
10. **Generate Laporan** — Export PDF atau Excel hasil penilaian + rekomendasi IDP

### Non-Fungsional
- **Usability:** UI mudah dipahami semua level pengguna
- **Security:** Data penilaian bersifat rahasia, akses sesuai role
- **Performance:** Proses data cepat
- **Reliability:** Stabil, minim error
- **Availability:** Bisa diakses kapan saja selama periode penilaian

---

## Acceptance Criteria (Sistem Diterima Jika)

- [ ] Seluruh proses penilaian berjalan digital tanpa error
- [ ] Perhitungan nilai otomatis akurat sesuai bobot
- [ ] Gap analysis tampil benar antar penilai
- [ ] Dashboard menampilkan data real-time
- [ ] Laporan dapat di-download
- [ ] Semua role dapat login dan mengakses fitur sesuai hak akses

---

## Urutan Pengerjaan yang Disarankan

1. Setup project Antigravity + struktur folder
2. Buat database & seed data dummy
3. Sistem autentikasi (login/logout + role-based redirect)
4. CRUD Karyawan (HR)
5. Manajemen Periode Penilaian
6. Form Penilaian AKHLAK (evaluator + self-assessment)
7. Engine perhitungan nilai otomatis
8. Dashboard + Gap Analysis + Chart
9. Generate Laporan
10. Testing & validasi input

---

## Catatan Penting

- Sections **5 (Interface Design)**, **6 (Testing)**, **7 (Implementation Plan)**, dan **8 (Source Code)** di dokumen template masih kosong — kamu harus mengisi semuanya
- Prototype low-fi dan high-fi (Figma/Adobe XD) perlu dibuat oleh tim secara terpisah
- Testing menggunakan **Black Box Testing** dengan test cases per fitur
- Referensi harus diisi dengan sumber yang relevan (bukan contoh placeholder)
