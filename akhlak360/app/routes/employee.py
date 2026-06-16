"""
app/routes/employee.py — Routes untuk Karyawan
Sistem Penilaian 360° Core Values AKHLAK
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import query_db, execute_db
from app.routes.auth import login_required, role_required
from datetime import datetime

employee_bp = Blueprint('employee', __name__)


# ============================================================
# ROUTE: Employee Dashboard
# ============================================================
@employee_bp.route('/dashboard')
@login_required
@role_required('karyawan')
def dashboard():
    """Dashboard karyawan — status self-assessment dan notifikasi."""
    user_id = session['user_id']

    # Periode aktif
    periode_aktif = query_db(
        "SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC LIMIT 1",
        one=True
    )

    self_assessment_status = None
    has_pending = False

    if periode_aktif:
        # Status self-assessment karyawan ini
        self_assessment = query_db(
            "SELECT * FROM penilaians WHERE id_period=? AND id_evaluator=? AND jenis_penilaian='self'",
            (periode_aktif['id_period'], user_id),
            one=True
        )
        self_assessment_status = self_assessment['status'] if self_assessment else None
        has_pending = self_assessment_status == 'pending'

    # Hasil penilaian terbaru
    hasil = query_db(
        """SELECT h.*, ap.period_name
           FROM hasil_akhirs h
           JOIN assessment_periods ap ON h.id_period = ap.id_period
           WHERE h.id_employee = ?
           ORDER BY h.calculated_at DESC LIMIT 3""",
        (user_id,)
    )

    return render_template('employee/dashboard.html',
        periode_aktif=periode_aktif,
        self_assessment_status=self_assessment_status,
        has_pending=has_pending,
        hasil=hasil
    )


# ============================================================
# ROUTE: Self-Assessment
# ============================================================
@employee_bp.route('/self-assessment', methods=['GET', 'POST'])
@login_required
@role_required('karyawan')
def self_assessment():
    """Form self-assessment karyawan."""
    user_id = session['user_id']

    # Ambil periode aktif
    periode = query_db(
        "SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC LIMIT 1",
        one=True
    )
    if not periode:
        flash('Tidak ada periode penilaian aktif saat ini.', 'warning')
        return redirect(url_for('employee.dashboard'))

    # Cari penilaian self
    penilaian = query_db(
        "SELECT * FROM penilaians WHERE id_period=? AND id_evaluator=? AND jenis_penilaian='self'",
        (periode['id_period'], user_id),
        one=True
    )
    if not penilaian:
        flash('Tidak ada tugas self-assessment untuk periode ini.', 'warning')
        return redirect(url_for('employee.dashboard'))

    if penilaian['status'] == 'submitted':
        flash('Self-assessment sudah disubmit.', 'info')
        return redirect(url_for('employee.my_results'))

    # Ambil semua indikator dikelompokkan per core value
    indikators = query_db(
        "SELECT * FROM indikators ORDER BY core_value, id_indikator"
    )

    # Nilai core value labels
    core_value_labels = {
        1: 'Amanah', 2: 'Kompeten', 3: 'Harmonis',
        4: 'Loyal', 5: 'Adaptif', 6: 'Kolaboratif'
    }

    # Kelompokkan indikator per core value
    grouped = {}
    for ind in indikators:
        cv = ind['core_value']
        if cv not in grouped:
            grouped[cv] = {'label': core_value_labels.get(cv, str(cv)), 'indikators': []}
        grouped[cv]['indikators'].append(ind)

    # Ambil draft yang sudah diisi (jika ada)
    existing_scores = {}
    details = query_db(
        "SELECT * FROM detail_penilaians WHERE penilaian_id=?",
        (penilaian['id_penilaian'],)
    )
    for d in details:
        existing_scores[d['id_indikator']] = d['score']

    if request.method == 'POST':
        action = request.form.get('action', 'draft')
        scores = {}
        feedbacks = {}

        # Kumpulkan semua nilai
        for ind in indikators:
            key = f'score_{ind["id_indikator"]}'
            score_val = request.form.get(key)
            if score_val:
                scores[ind['id_indikator']] = int(score_val)
            feedback_key = f'feedback_{ind["core_value"]}'
            feedbacks[ind['core_value']] = request.form.get(feedback_key, '')

        # Validasi: semua indikator harus diisi saat submit
        if action == 'submit':
            missing = [ind['id_indikator'] for ind in indikators if ind['id_indikator'] not in scores]
            if missing:
                flash('Semua indikator harus diisi sebelum submit.', 'danger')
                return render_template('employee/self_assessment.html',
                    penilaian=penilaian, grouped=grouped,
                    existing_scores=scores, periode=periode
                )

        # Simpan/update detail penilaian
        execute_db("DELETE FROM detail_penilaians WHERE penilaian_id=?", (penilaian['id_penilaian'],))
        for id_ind, score_val in scores.items():
            ind_obj = next((i for i in indikators if i['id_indikator'] == id_ind), None)
            cv = ind_obj['core_value'] if ind_obj else None
            fb = feedbacks.get(cv, '') if cv else ''
            execute_db(
                "INSERT INTO detail_penilaians (penilaian_id, id_indikator, score, feedback) VALUES (?,?,?,?)",
                (penilaian['id_penilaian'], id_ind, score_val, fb)
            )

        if action == 'submit':
            execute_db(
                "UPDATE penilaians SET status='submitted', submitted_at=? WHERE id_penilaian=?",
                (datetime.now().isoformat(), penilaian['id_penilaian'])
            )
            flash('Self-assessment berhasil disubmit!', 'success')
            return redirect(url_for('employee.my_results'))
        else:
            flash('Draft berhasil disimpan.', 'info')
            return redirect(url_for('employee.self_assessment'))

    return render_template('employee/self_assessment.html',
        penilaian=penilaian,
        grouped=grouped,
        existing_scores=existing_scores,
        periode=periode
    )


# ============================================================
# ROUTE: Hasil Penilaian Karyawan
# ============================================================
@employee_bp.route('/my-results')
@login_required
@role_required('karyawan')
def my_results():
    """Hasil penilaian + gap analysis + rekomendasi IDP."""
    user_id   = session['user_id']
    id_period = request.args.get('id_period')

    periods_list = query_db(
        """SELECT DISTINCT ap.* FROM assessment_periods ap
           JOIN hasil_akhirs h ON ap.id_period = h.id_period
           WHERE h.id_employee = ?
           ORDER BY ap.start_date DESC""",
        (user_id,)
    )

    hasil = None
    radar_data = None
    gap_analysis = []
    idp_rekomendasi = []

    if id_period:
        hasil = query_db(
            """SELECT h.*, ap.period_name FROM hasil_akhirs h
               JOIN assessment_periods ap ON h.id_period = ap.id_period
               WHERE h.id_employee=? AND h.id_period=?""",
            (user_id, id_period),
            one=True
        )

        if hasil:
            # Data radar chart: skor per jenis per core value
            core_value_labels = ['Amanah', 'Kompeten', 'Harmonis', 'Loyal', 'Adaptif', 'Kolaboratif']
            radar_data = {'labels': core_value_labels, 'datasets': {}}

            for jenis in ['atasan', 'bawahan', 'rekan', 'self']:
                scores_per_cv = []
                for cv in range(1, 7):
                    avg = query_db(
                        """SELECT AVG(dp.score) as avg_score
                           FROM detail_penilaians dp
                           JOIN penilaians p ON dp.penilaian_id = p.id_penilaian
                           JOIN indikators i ON dp.id_indikator = i.id_indikator
                           WHERE p.id_karyawan=? AND p.id_period=? AND p.jenis_penilaian=?
                             AND p.status='submitted' AND i.core_value=?""",
                        (user_id, id_period, jenis, cv),
                        one=True
                    )
                    scores_per_cv.append(round(avg['avg_score'], 2) if avg and avg['avg_score'] else 0)
                radar_data['datasets'][jenis] = scores_per_cv

            # Gap analysis per core value
            for i, cv_label in enumerate(core_value_labels):
                row = {'core_value': cv_label}
                for jenis in ['atasan', 'bawahan', 'rekan', 'self']:
                    row[jenis] = radar_data['datasets'][jenis][i]
                # Gap = max - min dari yang tersedia
                vals = [row[j] for j in ['atasan', 'bawahan', 'rekan', 'self'] if row[j] > 0]
                row['gap'] = round(max(vals) - min(vals), 2) if len(vals) > 1 else 0
                gap_analysis.append(row)

            # Rekomendasi IDP berdasarkan core value terendah
            if gap_analysis:
                # Hitung rata-rata per core value
                cv_avgs = []
                for ga in gap_analysis:
                    vals = [ga[j] for j in ['atasan', 'bawahan', 'rekan', 'self'] if ga[j] > 0]
                    avg_val = sum(vals) / len(vals) if vals else 0
                    cv_avgs.append({'cv': ga['core_value'], 'avg': avg_val})

                # Urutkan dari terendah
                cv_avgs.sort(key=lambda x: x['avg'])
                idp_map = {
                    'Amanah':      'Ikuti pelatihan manajemen waktu dan integritas kerja.',
                    'Kompeten':    'Daftarkan diri ke program sertifikasi dan pelatihan teknis.',
                    'Harmonis':    'Ikuti workshop komunikasi efektif dan team building.',
                    'Loyal':       'Pahami lebih dalam visi-misi perusahaan dan regulasi BUMN.',
                    'Adaptif':     'Ikuti seminar inovasi dan manajemen perubahan.',
                    'Kolaboratif': 'Aktifkan keterlibatan dalam proyek lintas divisi.',
                }
                for item in cv_avgs[:3]:  # Top 3 terendah
                    if item['avg'] < 4.0:
                        idp_rekomendasi.append({
                            'core_value': item['cv'],
                            'avg': item['avg'],
                            'rekomendasi': idp_map.get(item['cv'], '')
                        })

    elif periods_list:
        # Default ke periode terbaru
        return redirect(url_for('employee.my_results', id_period=periods_list[0]['id_period']))

    return render_template('employee/my_results.html',
        periods_list=periods_list,
        hasil=hasil,
        radar_data=radar_data,
        gap_analysis=gap_analysis,
        idp_rekomendasi=idp_rekomendasi,
        selected_period=id_period
    )
