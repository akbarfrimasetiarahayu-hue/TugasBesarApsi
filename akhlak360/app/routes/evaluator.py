"""
app/routes/evaluator.py — Routes untuk Evaluator
Sistem Penilaian 360° Core Values AKHLAK
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import query_db, execute_db
from app.routes.auth import login_required, role_required
from datetime import datetime

evaluator_bp = Blueprint('evaluator', __name__)


# ============================================================
# ROUTE: Evaluator Dashboard
# ============================================================
@evaluator_bp.route('/dashboard')
@login_required
@role_required('evaluator')
def dashboard():
    """Dashboard evaluator — daftar karyawan yang perlu dinilai."""
    user_id = session['user_id']

    # Periode aktif
    periode_aktif = query_db(
        "SELECT * FROM assessment_periods WHERE status='active' ORDER BY id_period DESC LIMIT 1",
        one=True
    )

    tugas_list = []
    has_pending = False

    if periode_aktif:
        tugas_list = query_db(
            """SELECT p.id_penilaian, p.jenis_penilaian, p.status, p.submitted_at,
                      e.nama as nama_karyawan, e.division, e.position
               FROM penilaians p
               JOIN employees e ON p.id_karyawan = e.user_id
               WHERE p.id_period = %s AND p.id_evaluator = %s AND p.jenis_penilaian != 'self'
               ORDER BY p.status ASC, e.nama ASC""",
            (periode_aktif['id_period'], user_id)
        )
        has_pending = any(t['status'] == 'pending' for t in tugas_list)

    return render_template('evaluator/dashboard.html',
        periode_aktif=periode_aktif,
        tugas_list=tugas_list,
        has_pending=has_pending
    )


# ============================================================
# ROUTE: Form Penilaian
# ============================================================
@evaluator_bp.route('/assess/<int:id_penilaian>', methods=['GET', 'POST'])
@login_required
@role_required('evaluator')
def assess(id_penilaian):
    """Form penilaian AKHLAK untuk karyawan tertentu."""
    user_id = session['user_id']

    # Validasi: penilaian ini milik evaluator ini
    penilaian = query_db(
        "SELECT * FROM penilaians WHERE id_penilaian=%s AND id_evaluator=%s",
        (id_penilaian, user_id),
        one=True
    )
    if not penilaian:
        flash('Penilaian tidak ditemukan atau bukan milik Anda.', 'danger')
        return redirect(url_for('evaluator.dashboard'))

    if penilaian['status'] == 'submitted':
        flash('Penilaian ini sudah disubmit.', 'info')
        return redirect(url_for('evaluator.dashboard'))

    # Ambil info karyawan yang dinilai
    karyawan = query_db(
        "SELECT * FROM employees WHERE user_id=%s",
        (penilaian['id_karyawan'],),
        one=True
    )

    # Ambil periode
    periode = query_db(
        "SELECT * FROM assessment_periods WHERE id_period=%s",
        (penilaian['id_period'],),
        one=True
    )

    # Ambil indikator dikelompokkan per core value
    indikators = query_db("SELECT * FROM indikators ORDER BY core_value, id_indikator")
    core_value_labels = {
        1: 'Amanah', 2: 'Kompeten', 3: 'Harmonis',
        4: 'Loyal', 5: 'Adaptif', 6: 'Kolaboratif'
    }
    grouped = {}
    for ind in indikators:
        cv = ind['core_value']
        if cv not in grouped:
            grouped[cv] = {'label': core_value_labels.get(cv, str(cv)), 'indikators': []}
        grouped[cv]['indikators'].append(ind)

    # Ambil draft yang sudah diisi
    existing_scores = {}
    existing_feedbacks = {}
    details = query_db(
        "SELECT dp.*, i.core_value FROM detail_penilaians dp JOIN indikators i ON dp.id_indikator = i.id_indikator WHERE dp.penilaian_id=%s",
        (id_penilaian,)
    )
    for d in details:
        existing_scores[d['id_indikator']] = d['score']
        if d['feedback']:
            existing_feedbacks[d['core_value']] = d['feedback']

    if request.method == 'POST':
        action = request.form.get('action', 'draft')
        scores = {}
        feedbacks = {}

        for ind in indikators:
            key = f'score_{ind["id_indikator"]}'
            score_val = request.form.get(key)
            if score_val:
                scores[ind['id_indikator']] = int(score_val)
            cv = ind['core_value']
            feedback_key = f'feedback_{cv}'
            if feedback_key not in feedbacks:
                feedbacks[cv] = request.form.get(feedback_key, '')

        # Validasi submit: semua indikator harus diisi
        if action == 'submit':
            missing = [ind['id_indikator'] for ind in indikators if ind['id_indikator'] not in scores]
            if missing:
                flash('Semua indikator harus diisi sebelum submit.', 'danger')
                return render_template('evaluator/assess.html',
                    penilaian=penilaian, karyawan=karyawan,
                    grouped=grouped, existing_scores=scores,
                    existing_feedbacks=feedbacks, periode=periode
                )

        # Simpan detail
        execute_db("DELETE FROM detail_penilaians WHERE penilaian_id=%s", (id_penilaian,))
        for id_ind, score_val in scores.items():
            ind_obj = next((i for i in indikators if i['id_indikator'] == id_ind), None)
            cv = ind_obj['core_value'] if ind_obj else None
            fb = feedbacks.get(cv, '')
            execute_db(
                "INSERT INTO detail_penilaians (penilaian_id, id_indikator, score, feedback) VALUES (%s,%s,%s,%s)",
                (id_penilaian, id_ind, score_val, fb)
            )

        if action == 'submit':
            execute_db(
                "UPDATE penilaians SET status='submitted', submitted_at=%s WHERE id_penilaian=%s",
                (datetime.now().isoformat(), id_penilaian)
            )
            # Cek apakah semua evaluator sudah submit → hitung otomatis
            from app.services.calculator import cek_dan_hitung_otomatis
            cek_dan_hitung_otomatis(penilaian['id_karyawan'], penilaian['id_period'])
            flash(f'Penilaian untuk {karyawan["nama"]} berhasil disubmit!', 'success')
            return redirect(url_for('evaluator.dashboard'))
        else:
            flash('Draft berhasil disimpan.', 'info')
            return redirect(url_for('evaluator.assess', id_penilaian=id_penilaian))

    return render_template('evaluator/assess.html',
        penilaian=penilaian,
        karyawan=karyawan,
        grouped=grouped,
        existing_scores=existing_scores,
        existing_feedbacks=existing_feedbacks,
        periode=periode
    )
