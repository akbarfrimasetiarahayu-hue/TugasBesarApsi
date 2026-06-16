"""
run.py — Entry point aplikasi AKHLAK 360°
Jalankan: python run.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  AKHLAK 360 - Sistem Penilaian Core Values")
    print("  PT. Energi Nusantara")
    print("  IS Project 2026 | FRI-086 | TI-47-08")
    print("=" * 60)
    print("  Server: http://127.0.0.1:5000")
    print("  Tekan CTRL+C untuk menghentikan server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
