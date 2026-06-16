"""
config.py — Konfigurasi aplikasi AKHLAK 360°
Sistem Penilaian 360° Core Values AKHLAK
PT. Energi Nusantara
"""

import os

# Direktori dasar proyek
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Konfigurasi utama aplikasi."""

    # Secret key untuk session Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'akhlak360-secret-key-energi-nusantara-2026')

    # Path database SQLite
    DATABASE = os.path.join(BASE_DIR, 'akhlak360.db')

    # Folder untuk file laporan yang di-generate
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'static', 'reports')

    # Konfigurasi session
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # Debug mode (nonaktifkan di production)
    DEBUG = True


class ProductionConfig(Config):
    """Konfigurasi untuk production."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Wajib set dari environment


# Konfigurasi yang aktif
config = Config()
