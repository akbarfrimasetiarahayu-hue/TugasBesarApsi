"""
app/services/calculator.py — Engine Perhitungan Nilai Akhir AKHLAK 360°
Mengimplementasikan formula weighted score:
  Atasan×0.40 + Bawahan×0.30 + Rekan×0.20 + Self×0.10
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from database import query_db, execute_db
from datetime import datetime


# Bobot penilaian sesuai foundation file
BOBOT = {
    'atasan':  0.40,
    'bawahan': 0.30,
    'rekan':   0.20,
    'self':    0.10,
}


def get_kategori(total_score: float) -> str:
    """
    Menentukan kategori berdasarkan total score.
    4.50 - 5.00 → Sangat Baik
    3.50 - 4.49 → Baik
    2.50 - 3.49 → Cukup
    < 2.50      → Kurang
    """
    if total_score is None:
        return 'Belum Dihitung'
    if total_score >= 4.50:
        return 'Sangat Baik'
    elif total_score >= 3.50:
        return 'Baik'
    elif total_score >= 2.50:
        return 'Cukup'
    else:
        return 'Kurang'


def hitung_nilai_akhir(id_karyawan: int, id_period: int) -> dict:
    """
    Hitung nilai akhir seorang karyawan untuk satu periode.

    Returns:
        dict: {
            'score_atasan': float | None,
            'score_bawahan': float | None,
            'score_rekan': float | None,
            'score_self': float | None,
            'total_score': float,
            'category': str
        }
    """
    scores = {}

    for jenis in ['atasan', 'bawahan', 'rekan', 'self']:
        # Ambil semua penilaian yang sudah disubmit untuk jenis ini
        result = query_db(
            """SELECT AVG(dp.score) as avg_score
               FROM detail_penilaians dp
               JOIN penilaians p ON dp.penilaian_id = p.id_penilaian
               WHERE p.id_karyawan = ? AND p.id_period = ?
                 AND p.jenis_penilaian = ? AND p.status = 'submitted'""",
            (id_karyawan, id_period, jenis),
            one=True
        )
        scores[jenis] = round(result['avg_score'], 4) if result and result['avg_score'] is not None else None

    # Hitung weighted total (hanya dari jenis yang tersedia)
    total = 0.0
    bobot_used = 0.0
    for jenis, bobot in BOBOT.items():
        if scores[jenis] is not None:
            total += scores[jenis] * bobot
            bobot_used += bobot

    # Normalisasi jika tidak semua jenis tersedia
    if bobot_used > 0 and bobot_used < 1.0:
        total = total / bobot_used

    total = round(total, 2)
    category = get_kategori(total)

    return {
        'score_atasan':  scores.get('atasan'),
        'score_bawahan': scores.get('bawahan'),
        'score_rekan':   scores.get('rekan'),
        'score_self':    scores.get('self'),
        'total_score':   total,
        'category':      category,
    }


def simpan_hasil(id_karyawan: int, id_period: int, hasil: dict) -> int:
    """Simpan atau update hasil akhir ke tabel hasil_akhirs."""
    existing = query_db(
        "SELECT id_result FROM hasil_akhirs WHERE id_employee=? AND id_period=?",
        (id_karyawan, id_period),
        one=True
    )

    now = datetime.now().isoformat()

    if existing:
        execute_db(
            """UPDATE hasil_akhirs
               SET score_atasan=?, score_bawahan=?, score_rekan=?, score_self=?,
                   total_score=?, category=?, calculated_at=?
               WHERE id_employee=? AND id_period=?""",
            (hasil['score_atasan'], hasil['score_bawahan'],
             hasil['score_rekan'], hasil['score_self'],
             hasil['total_score'], hasil['category'], now,
             id_karyawan, id_period)
        )
        return existing['id_result']
    else:
        return execute_db(
            """INSERT INTO hasil_akhirs
               (id_employee, id_period, score_atasan, score_bawahan, score_rekan, score_self,
                total_score, category, calculated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_karyawan, id_period,
             hasil['score_atasan'], hasil['score_bawahan'],
             hasil['score_rekan'], hasil['score_self'],
             hasil['total_score'], hasil['category'], now)
        )


def cek_dan_hitung_otomatis(id_karyawan: int, id_period: int):
    """
    Cek apakah semua evaluator sudah submit, jika ya hitung otomatis.
    Dipanggil setelah setiap submit penilaian.
    """
    # Cek apakah masih ada yang pending untuk karyawan ini
    pending = query_db(
        """SELECT COUNT(*) as cnt FROM penilaians
           WHERE id_karyawan=? AND id_period=? AND status='pending'""",
        (id_karyawan, id_period),
        one=True
    )['cnt']

    if pending == 0:
        # Semua sudah submit, hitung nilai akhir
        hasil = hitung_nilai_akhir(id_karyawan, id_period)
        simpan_hasil(id_karyawan, id_period, hasil)
        print(f"[AUTO-CALC] Nilai karyawan {id_karyawan} periode {id_period}: {hasil['total_score']} ({hasil['category']})")
        return True
    return False


def hitung_semua_karyawan(id_period: int) -> int:
    """
    Hitung nilai akhir untuk SEMUA karyawan dalam satu periode.
    Dipanggil oleh HR secara manual.
    """
    # Ambil semua karyawan yang ada penilaiannya di periode ini
    karyawans = query_db(
        "SELECT DISTINCT id_karyawan FROM penilaians WHERE id_period=?",
        (id_period,)
    )

    count = 0
    for k in karyawans:
        hasil = hitung_nilai_akhir(k['id_karyawan'], id_period)
        simpan_hasil(k['id_karyawan'], id_period, hasil)
        count += 1

    return count
