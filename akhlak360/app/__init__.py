"""
app/__init__.py — Inisialisasi aplikasi Flask AKHLAK 360°
"""

from flask import Flask
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def create_app():
    """Application factory untuk Flask."""
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='../static'
    )

    # Load konfigurasi
    from config import config
    app.secret_key = config.SECRET_KEY
    app.config['DATABASE'] = config.DATABASE
    app.config['REPORTS_FOLDER'] = config.REPORTS_FOLDER

    # Buat folder laporan jika belum ada
    os.makedirs(config.REPORTS_FOLDER, exist_ok=True)

    # Register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.hr import hr_bp
    from app.routes.employee import employee_bp
    from app.routes.evaluator import evaluator_bp
    from app.routes.management import management_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(evaluator_bp, url_prefix='/evaluator')
    app.register_blueprint(management_bp, url_prefix='/management')

    return app
