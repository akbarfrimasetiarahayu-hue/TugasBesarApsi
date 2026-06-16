"""
app/services/notifier.py — Layanan Notifikasi & Reminder
Sistem Penilaian 360° Core Values AKHLAK
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from database import query_db


def get_pending_users(id_period: int) -> list:
    """
    Mengembalikan daftar user yang belum submit penilaian untuk periode tertentu.

    Returns:
        list of dict: [{nama, email, division, jenis_penilaian, id_karyawan_nama}]
    """
    pending = query_db(
        """SELECT DISTINCT e.nama, e.email, e.division,
                  p.jenis_penilaian,
                  ka.nama as nama_karyawan
           FROM penilaians p
           JOIN employees e ON p.id_evaluator = e.user_id
           JOIN employees ka ON p.id_karyawan = ka.user_id
           WHERE p.id_period = ? AND p.status = 'pending'
           ORDER BY e.nama""",
        (id_period,)
    )
    return pending


def simulate_send_reminder(id_period: int) -> int:
    """
    Simulasi pengiriman reminder ke semua pengguna yang belum submit.
    Dalam implementasi nyata, ini akan mengirim email.

    Returns:
        int: jumlah reminder yang dikirim
    """
    pending_users = get_pending_users(id_period)
    count = len(pending_users)

    for user in pending_users:
        # Simulasi log pengiriman reminder
        print(f"[REMINDER] Kirim ke {user['email']}: "
              f"Reminder penilaian {user['jenis_penilaian']} untuk {user['nama_karyawan']}")

    print(f"[NOTIFIER] Total {count} reminder terkirim (simulasi) untuk periode {id_period}")
    return count


def check_user_pending(user_id: int, id_period: int) -> bool:
    """
    Cek apakah user tertentu masih memiliki penilaian pending.

    Returns:
        bool: True jika masih ada yang pending
    """
    result = query_db(
        """SELECT COUNT(*) as cnt FROM penilaians
           WHERE id_evaluator = ? AND id_period = ? AND status = 'pending'""",
        (user_id, id_period),
        one=True
    )
    return result['cnt'] > 0 if result else False
