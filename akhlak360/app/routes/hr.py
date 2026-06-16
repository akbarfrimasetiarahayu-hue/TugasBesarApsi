"""
app/routes/hr.py — Routes untuk HR Admin
Sistem Penilaian 360° Core Values AKHLAK
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import query_db, execute_db, get_db
from app.routes.auth import login_required, role_required


hr_bp = Blueprint('hr', __name__)


# ============================================================
# ROUTE: HR Dashboard
# ============================================================
@hr_bp.route('/dashboard')
@login_required
@role_required('hr')
def dashboard():
    """Dashboard HR — statistik dan ringkasan penilaian."""
    # Statistik karyawan
    total_karyawan = query_db("SELECT COUNT(*) as cnt FROM employees", one=True)['cnt']

    # Periode aktif
    periode_aktif = query_db(
        "SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC LIMIT 1",
        one=True
    )

    # Penilaian pending dan selesai
    total_pending = 0
    total_selesai = 0
    completion_by_division = []
    pending_users = []

    if periode_aktif:
        total_pending = query_db(
            "SELECT COUNT(*) as cnt FROM penilaians WHERE id_period=? AND status='pending'",
            (periode_aktif['id_period'],), one=True
        )['cnt']
        total_selesai = query_db(
            "SELECT COUNT(*) as cnt FROM penilaians WHERE id_period=? AND status='submitted'",
            (periode_aktif['id_period'],), one=True
        )['cnt']

        # Completion per divisi
        completion_by_division = query_db(
            """SELECT e.division,
                      COUNT(p.id_penilaian) as total,
                      SUM(CASE WHEN p.status='submitted' THEN 1 ELSE 0 END) as selesai
               FROM penilaians p
               JOIN employees e ON p.id_evaluator = e.user_id
               WHERE p.id_period = ?
               GROUP BY e.division""",
            (periode_aktif['id_period'],)
        )

        # User yang belum mengisi
        pending_users = query_db(
            """SELECT DISTINCT e.nama, e.email, e.division, p.jenis_penilaian
               FROM penilaians p
               JOIN employees e ON p.id_evaluator = e.user_id
               WHERE p.id_period = ? AND p.status = 'pending'
               LIMIT 10""",
            (periode_aktif['id_period'],)
        )

    # Hasil penilaian terbaru
    hasil_terbaru = query_db(
        """SELECT h.*, e.nama, e.division, ap.period_name
           FROM hasil_akhirs h
           JOIN employees e ON h.id_employee = e.user_id
           JOIN assessment_periods ap ON h.id_period = ap.id_period
           ORDER BY h.calculated_at DESC LIMIT 10"""
    )

    return render_template('hr/dashboard.html',
        total_karyawan=total_karyawan,
        periode_aktif=periode_aktif,
        total_pending=total_pending,
        total_selesai=total_selesai,
        completion_by_division=completion_by_division,
        pending_users=pending_users,
        hasil_terbaru=hasil_terbaru
    )


# ============================================================
# ROUTE: Kelola Karyawan — CRUD
# ============================================================
@hr_bp.route('/employees')
@login_required
@role_required('hr')
def employees():
    """Daftar karyawan."""
    search = request.args.get('search', '')
    if search:
        daftar = query_db(
            """SELECT e.*, sup.nama as nama_supervisor
               FROM employees e
               LEFT JOIN employees sup ON e.id_supervisor = sup.user_id
               WHERE e.nama LIKE ? OR e.nip LIKE ? OR e.division LIKE ?
               ORDER BY e.nama""",
            (f'%{search}%', f'%{search}%', f'%{search}%')
        )
    else:
        daftar = query_db(
            """SELECT e.*, sup.nama as nama_supervisor
               FROM employees e
               LEFT JOIN employees sup ON e.id_supervisor = sup.user_id
               ORDER BY e.nama"""
        )
    all_employees = query_db("SELECT user_id, nama FROM employees ORDER BY nama")
    return render_template('hr/employees.html',
        daftar=daftar,
        all_employees=all_employees,
        search=search
    )


@hr_bp.route('/employees/add', methods=['POST'])
@login_required
@role_required('hr')
def employee_add():
    """Tambah karyawan baru."""
    nama      = request.form.get('nama', '').strip()
    email     = request.form.get('email', '').strip()
    nip       = request.form.get('nip', '').strip()
    position  = request.form.get('position', '').strip()
    division  = request.form.get('division', '').strip()
    id_sup    = request.form.get('id_supervisor') or None

    # Validasi wajib
    if not all([nama, email, nip, position, division]):
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('hr.employees'))

    # Cek duplikat NIP
    if query_db("SELECT user_id FROM employees WHERE nip=?", (nip,), one=True):
        flash('NIP sudah terdaftar.', 'danger')
        return redirect(url_for('hr.employees'))

    # Cek duplikat email
    if query_db("SELECT user_id FROM employees WHERE email=?", (email,), one=True):
        flash('Email sudah terdaftar.', 'danger')
        return redirect(url_for('hr.employees'))

    execute_db(
        "INSERT INTO employees (nama, email, nip, position, division, id_supervisor) VALUES (?, ?, ?, ?, ?, ?)",
        (nama, email, nip, position, division, id_sup)
    )
    flash(f'Karyawan {nama} berhasil ditambahkan.', 'success')
    return redirect(url_for('hr.employees'))


@hr_bp.route('/employees/edit/<int:user_id>', methods=['POST'])
@login_required
@role_required('hr')
def employee_edit(user_id):
    """Edit data karyawan."""
    nama     = request.form.get('nama', '').strip()
    email    = request.form.get('email', '').strip()
    nip      = request.form.get('nip', '').strip()
    position = request.form.get('position', '').strip()
    division = request.form.get('division', '').strip()
    id_sup   = request.form.get('id_supervisor') or None

    if not all([nama, email, nip, position, division]):
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('hr.employees'))

    # Cek duplikat NIP (exclude diri sendiri)
    dup_nip = query_db("SELECT user_id FROM employees WHERE nip=? AND user_id!=?", (nip, user_id), one=True)
    if dup_nip:
        flash('NIP sudah digunakan karyawan lain.', 'danger')
        return redirect(url_for('hr.employees'))

    # Cek duplikat email
    dup_email = query_db("SELECT user_id FROM employees WHERE email=? AND user_id!=?", (email, user_id), one=True)
    if dup_email:
        flash('Email sudah digunakan karyawan lain.', 'danger')
        return redirect(url_for('hr.employees'))

    execute_db(
        "UPDATE employees SET nama=?, email=?, nip=?, position=?, division=?, id_supervisor=? WHERE user_id=?",
        (nama, email, nip, position, division, id_sup, user_id)
    )
    flash(f'Data karyawan berhasil diperbarui.', 'success')
    return redirect(url_for('hr.employees'))


@hr_bp.route('/employees/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('hr')
def employee_delete(user_id):
    """Hapus karyawan."""
    karyawan = query_db("SELECT nama FROM employees WHERE user_id=?", (user_id,), one=True)
    if not karyawan:
        flash('Karyawan tidak ditemukan.', 'danger')
        return redirect(url_for('hr.employees'))

    execute_db("DELETE FROM user_accounts WHERE id_employee=?", (user_id,))
    execute_db("DELETE FROM employees WHERE user_id=?", (user_id,))
    flash(f'Karyawan {karyawan["nama"]} berhasil dihapus.', 'success')
    return redirect(url_for('hr.employees'))


# ============================================================
# ROUTE: Periode Penilaian — CRUD
# ============================================================
@hr_bp.route('/periods')
@login_required
@role_required('hr')
def periods():
    """Daftar periode penilaian."""
    daftar = query_db("SELECT * FROM assessment_periods ORDER BY start_date DESC")
    return render_template('hr/periods.html', daftar=daftar)


@hr_bp.route('/periods/add', methods=['POST'])
@login_required
@role_required('hr')
def period_add():
    """Tambah periode penilaian baru."""
    period_name = request.form.get('period_name', '').strip()
    start_date  = request.form.get('start_date', '').strip()
    end_date    = request.form.get('end_date', '').strip()

    if not all([period_name, start_date, end_date]):
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('hr.periods'))

    if end_date <= start_date:
        flash('Tanggal selesai harus setelah tanggal mulai.', 'danger')
        return redirect(url_for('hr.periods'))

    execute_db(
        "INSERT INTO assessment_periods (period_name, start_date, end_date, status) VALUES (?, ?, ?, 'draft')",
        (period_name, start_date, end_date)
    )
    flash(f'Periode "{period_name}" berhasil ditambahkan.', 'success')
    return redirect(url_for('hr.periods'))


@hr_bp.route('/periods/edit/<int:id_period>', methods=['POST'])
@login_required
@role_required('hr')
def period_edit(id_period):
    """Edit periode penilaian."""
    period_name = request.form.get('period_name', '').strip()
    start_date  = request.form.get('start_date', '').strip()
    end_date    = request.form.get('end_date', '').strip()
    status      = request.form.get('status', 'draft').strip()

    if end_date <= start_date:
        flash('Tanggal selesai harus setelah tanggal mulai.', 'danger')
        return redirect(url_for('hr.periods'))

    execute_db(
        "UPDATE assessment_periods SET period_name=?, start_date=?, end_date=?, status=? WHERE id_period=?",
        (period_name, start_date, end_date, status, id_period)
    )
    flash('Periode berhasil diperbarui.', 'success')
    return redirect(url_for('hr.periods'))


@hr_bp.route('/periods/delete/<int:id_period>', methods=['POST'])
@login_required
@role_required('hr')
def period_delete(id_period):
    """Hapus periode penilaian."""
    execute_db("DELETE FROM assessment_periods WHERE id_period=?", (id_period,))
    flash('Periode berhasil dihapus.', 'success')
    return redirect(url_for('hr.periods'))


# ============================================================
# ROUTE: Assign Evaluator
# ============================================================
@hr_bp.route('/assign', methods=['GET', 'POST'])
@login_required
@role_required('hr')
def assign():
    """Auto-assign evaluator berdasarkan struktur organisasi."""
    periods_list = query_db("SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC")

    if request.method == 'POST':
        id_period = request.form.get('id_period')
        if not id_period:
            flash('Pilih periode terlebih dahulu.', 'danger')
            return redirect(url_for('hr.assign'))

        id_period = int(id_period)
        employees_list = query_db(
            "SELECT user_id, nama, division, id_supervisor FROM employees ORDER BY nama"
        )

        # Hapus assignment lama untuk periode ini
        execute_db("DELETE FROM penilaians WHERE id_period=?", (id_period,))

        count = 0
        for emp in employees_list:
            emp_id   = emp['user_id']
            emp_div  = emp['division']
            emp_sup  = emp['id_supervisor']

            # SELF assessment
            execute_db(
                "INSERT INTO penilaians (id_period, id_evaluator, id_karyawan, jenis_penilaian, status) VALUES (?,?,?,'self','pending')",
                (id_period, emp_id, emp_id)
            )
            count += 1

            # ATASAN — jika punya supervisor
            if emp_sup:
                execute_db(
                    "INSERT INTO penilaians (id_period, id_evaluator, id_karyawan, jenis_penilaian, status) VALUES (?,?,?,'atasan','pending')",
                    (id_period, emp_sup, emp_id)
                )
                count += 1

            # BAWAHAN — semua karyawan yang menggunakan emp sebagai supervisor
            bawahans = query_db(
                "SELECT user_id FROM employees WHERE id_supervisor=? AND user_id!=?",
                (emp_id, emp_id)
            )
            for b in bawahans:
                execute_db(
                    "INSERT INTO penilaians (id_period, id_evaluator, id_karyawan, jenis_penilaian, status) VALUES (?,?,?,'bawahan','pending')",
                    (id_period, b['user_id'], emp_id)
                )
                count += 1

            # REKAN — karyawan divisi sama, bukan atasan/bawahan, bukan diri sendiri
            bawahan_ids = [b['user_id'] for b in bawahans]
            exclude_ids = bawahan_ids + ([emp_sup] if emp_sup else []) + [emp_id]
            rekans = query_db(
                "SELECT user_id FROM employees WHERE division=? AND user_id NOT IN ({})".format(
                    ','.join('?' * len(exclude_ids))
                ),
                [emp_div] + exclude_ids
            )
            for r in rekans:
                execute_db(
                    "INSERT INTO penilaians (id_period, id_evaluator, id_karyawan, jenis_penilaian, status) VALUES (?,?,?,'rekan','pending')",
                    (id_period, r['user_id'], emp_id)
                )
                count += 1

        flash(f'Berhasil assign {count} penilaian untuk periode ini.', 'success')
        return redirect(url_for('hr.assign'))

    # GET — preview assignment
    selected_period = request.args.get('id_period')
    preview = []
    if selected_period:
        preview = query_db(
            """SELECT p.id_penilaian, p.jenis_penilaian, p.status,
                      ev.nama as nama_evaluator, ev.division as div_evaluator,
                      ka.nama as nama_karyawan
               FROM penilaians p
               JOIN employees ev ON p.id_evaluator = ev.user_id
               JOIN employees ka ON p.id_karyawan = ka.user_id
               WHERE p.id_period = ?
               ORDER BY ka.nama, p.jenis_penilaian""",
            (selected_period,)
        )

    return render_template('hr/assign.html',
        periods_list=periods_list,
        preview=preview,
        selected_period=selected_period
    )


# ============================================================
# ROUTE: Kirim Reminder
# ============================================================
@hr_bp.route('/reminder', methods=['POST'])
@login_required
@role_required('hr')
def send_reminder():
    """Simulasi kirim reminder ke user yang belum submit."""
    id_period = request.form.get('id_period')
    if not id_period:
        flash('Periode tidak valid.', 'danger')
        return redirect(url_for('hr.dashboard'))

    pending_count = query_db(
        "SELECT COUNT(*) as cnt FROM penilaians WHERE id_period=? AND status='pending'",
        (id_period,), one=True
    )['cnt']

    # Simulasi: log reminder (tanpa kirim email asli)
    print(f"[REMINDER] {pending_count} penilaian pending untuk periode {id_period} — notifikasi dikirim (simulasi)")
    flash(f'Reminder berhasil dikirim ke {pending_count} pengguna yang belum mengisi penilaian.', 'success')
    return redirect(url_for('hr.dashboard'))


# ============================================================
# ROUTE: Hasil Penilaian
# ============================================================
@hr_bp.route('/results')
@login_required
@role_required('hr')
def results():
    """Tabel semua hasil penilaian."""
    id_period = request.args.get('id_period', '')
    division  = request.args.get('division', '')

    query = """SELECT h.*, e.nama, e.nip, e.division, ap.period_name
               FROM hasil_akhirs h
               JOIN employees e ON h.id_employee = e.user_id
               JOIN assessment_periods ap ON h.id_period = ap.id_period
               WHERE 1=1"""
    params = []
    if id_period:
        query += " AND h.id_period = ?"
        params.append(id_period)
    if division:
        query += " AND e.division = ?"
        params.append(division)
    query += " ORDER BY h.total_score DESC"

    hasil = query_db(query, params)
    periods_list = query_db("SELECT * FROM assessment_periods ORDER BY start_date DESC")
    divisions = query_db("SELECT DISTINCT division FROM employees ORDER BY division")

    return render_template('hr/results.html',
        hasil=hasil,
        periods_list=periods_list,
        divisions=divisions,
        selected_period=id_period,
        selected_division=division
    )


# ============================================================
# ROUTE: Hitung Nilai (trigger manual oleh HR)
# ============================================================
@hr_bp.route('/calculate/<int:id_period>', methods=['POST'])
@login_required
@role_required('hr')
def calculate(id_period):
    """Trigger manual perhitungan nilai akhir untuk semua karyawan di periode ini."""
    from app.services.calculator import hitung_semua_karyawan
    count = hitung_semua_karyawan(id_period)
    flash(f'Nilai akhir berhasil dihitung untuk {count} karyawan.', 'success')
    return redirect(url_for('hr.results'))


# ============================================================
# ROUTE: Laporan
# ============================================================
@hr_bp.route('/reports')
@login_required
@role_required('hr')
def reports():
    """Halaman generate laporan."""
    periods_list = query_db("SELECT * FROM assessment_periods ORDER BY start_date DESC")
    report_logs  = query_db(
        """SELECT hr.*, ap.period_name, e.nama as generated_by_nama
           FROM hasil_reports hr
           JOIN assessment_periods ap ON hr.id_period = ap.id_period
           LEFT JOIN employees e ON hr.generated_by = e.user_id
           ORDER BY hr.generate_date DESC LIMIT 20"""
    )
    return render_template('hr/reports.html', periods_list=periods_list, report_logs=report_logs)


@hr_bp.route('/reports/generate', methods=['POST'])
@login_required
@role_required('hr')
def generate_report():
    """Generate laporan PDF atau Excel."""
    id_period   = request.form.get('id_period')
    report_type = request.form.get('report_type', 'excel')

    if not id_period:
        flash('Pilih periode terlebih dahulu.', 'danger')
        return redirect(url_for('hr.reports'))

    from app.services.report_gen import generate_excel, generate_pdf
    from flask import send_file

    periode = query_db("SELECT * FROM assessment_periods WHERE id_period=?", (id_period,), one=True)
    if not periode:
        flash('Periode tidak ditemukan.', 'danger')
        return redirect(url_for('hr.reports'))

    employee_id = session.get('user_id')

    if report_type == 'pdf':
        file_path = generate_pdf(int(id_period), employee_id)
        mime = 'application/pdf'
        ext  = 'pdf'
    else:
        file_path = generate_excel(int(id_period), employee_id)
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ext  = 'xlsx'

    return send_file(file_path, mimetype=mime, as_attachment=True,
                     download_name=f'Laporan_AKHLAK_{periode["period_name"]}.{ext}')
