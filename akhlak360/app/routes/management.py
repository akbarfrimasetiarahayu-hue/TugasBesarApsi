"""
app/routes/management.py — Routes untuk Management
Sistem Penilaian 360° Core Values AKHLAK
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import query_db
from app.routes.auth import login_required, role_required

management_bp = Blueprint('management', __name__)


@management_bp.route('/dashboard')
@login_required
@role_required('management')
def dashboard():
    """Dashboard Management — overview dan distribusi penilaian."""
    # Statistik umum
    total_karyawan = query_db("SELECT COUNT(*) as cnt FROM employees", one=True)['cnt']

    periode_aktif = query_db(
        "SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC LIMIT 1",
        one=True
    )

    # Distribusi kategori
    distribusi_kategori = []
    top_performers = []
    bottom_performers = []
    division_stats = []

    if periode_aktif:
        pid = periode_aktif['id_period']
        distribusi_kategori = query_db(
            """SELECT category, COUNT(*) as jumlah FROM hasil_akhirs
               WHERE id_period=%s AND category IS NOT NULL
               GROUP BY category""",
            (pid,)
        )
        top_performers = query_db(
            """SELECT h.total_score, h.category, e.nama, e.division, e.position
               FROM hasil_akhirs h JOIN employees e ON h.id_employee=e.user_id
               WHERE h.id_period=%s AND h.total_score IS NOT NULL
               ORDER BY h.total_score DESC LIMIT 5""",
            (pid,)
        )
        bottom_performers = query_db(
            """SELECT h.total_score, h.category, e.nama, e.division, e.position
               FROM hasil_akhirs h JOIN employees e ON h.id_employee=e.user_id
               WHERE h.id_period=%s AND h.total_score IS NOT NULL
               ORDER BY h.total_score ASC LIMIT 5""",
            (pid,)
        )
        division_stats = query_db(
            """SELECT e.division, AVG(h.total_score) as avg_score, COUNT(h.id_result) as jumlah
               FROM hasil_akhirs h JOIN employees e ON h.id_employee=e.user_id
               WHERE h.id_period=%s
               GROUP BY e.division ORDER BY avg_score DESC""",
            (pid,)
        )

    return render_template('management/dashboard.html',
        total_karyawan=total_karyawan,
        periode_aktif=periode_aktif,
        distribusi_kategori=distribusi_kategori,
        top_performers=top_performers,
        bottom_performers=bottom_performers,
        division_stats=division_stats
    )


@management_bp.route('/performance')
@login_required
@role_required('management')
def performance():
    """Performance review semua karyawan."""
    id_period = request.args.get('id_period', '')
    division  = request.args.get('division', '')

    query = """SELECT h.*, e.nama, e.nip, e.division, e.position, ap.period_name
               FROM hasil_akhirs h
               JOIN employees e ON h.id_employee=e.user_id
               JOIN assessment_periods ap ON h.id_period=ap.id_period
               WHERE 1=1"""
    params = []
    if id_period:
        query += " AND h.id_period=%s"
        params.append(id_period)
    if division:
        query += " AND e.division=%s"
        params.append(division)
    query += " ORDER BY h.total_score DESC"

    hasil = query_db(query, params)
    periods_list = query_db("SELECT * FROM assessment_periods ORDER BY start_date DESC")
    divisions = query_db("SELECT DISTINCT division FROM employees ORDER BY division")

    return render_template('management/performance.html',
        hasil=hasil,
        periods_list=periods_list,
        divisions=divisions,
        selected_period=id_period,
        selected_division=division
    )


@management_bp.route('/reports')
@login_required
@role_required('management')
def reports():
    """Halaman laporan untuk management."""
    periods_list = query_db("SELECT * FROM assessment_periods ORDER BY start_date DESC")
    return render_template('management/reports.html', periods_list=periods_list)


@management_bp.route('/reports/generate', methods=['POST'])
@login_required
@role_required('management')
def generate_report():
    """Generate laporan PDF atau Excel."""
    id_period   = request.form.get('id_period')
    report_type = request.form.get('report_type', 'excel')

    if not id_period:
        flash('Pilih periode terlebih dahulu.', 'danger')
        return redirect(url_for('management.reports'))

    from app.services.report_gen import generate_excel, generate_pdf
    periode = query_db("SELECT * FROM assessment_periods WHERE id_period=%s", (id_period,), one=True)

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
