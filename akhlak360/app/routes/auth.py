"""
app/routes/auth.py — Autentikasi: Login, Logout
Sistem Penilaian 360° Core Values AKHLAK
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import bcrypt
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database import query_db
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# ============================================================
# DECORATOR: login_required
# ============================================================
def login_required(f):
    """Decorator untuk memastikan user sudah login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Decorator untuk memeriksa role user."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Silakan login terlebih dahulu.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
                return redirect(url_for('auth.unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================
# ROUTE: GET /login & POST /login
# ============================================================
@auth_bp.route('/', methods=['GET'])
def index():
    """Redirect root ke login."""
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login — validasi email/username + password bcrypt."""
    # Jika sudah login, redirect ke dashboard
    if 'user_id' in session:
        return redirect_by_role(session.get('role'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username dan password wajib diisi.', 'danger')
            return render_template('login.html')

        # Cari akun berdasarkan username
        account = query_db(
            """SELECT ua.id_account, ua.password, ua.status,
                      e.user_id, e.nama, e.email, e.division,
                      r.role_name
               FROM user_accounts ua
               JOIN employees e ON ua.id_employee = e.user_id
               JOIN roles r ON ua.id_role = r.id_role
               WHERE ua.username = ? AND ua.status = 'active'""",
            (username,),
            one=True
        )

        if not account:
            flash('Username atau password salah.', 'danger')
            return render_template('login.html')

        # Verifikasi password dengan bcrypt
        password_match = bcrypt.checkpw(
            password.encode('utf-8'),
            account['password'].encode('utf-8')
        )

        if not password_match:
            flash('Username atau password salah.', 'danger')
            return render_template('login.html')

        # Set session
        session.permanent = False
        session['user_id']   = account['user_id']
        session['account_id'] = account['id_account']
        session['role']      = account['role_name']
        session['nama']      = account['nama']
        session['email']     = account['email']
        session['division']  = account['division']

        flash(f'Selamat datang, {account["nama"]}!', 'success')
        return redirect_by_role(account['role_name'])

    return render_template('login.html')


# ============================================================
# ROUTE: GET /logout
# ============================================================
@auth_bp.route('/logout')
def logout():
    """Clear session dan redirect ke login."""
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('auth.login'))


# ============================================================
# ROUTE: Halaman 403 — Unauthorized
# ============================================================
@auth_bp.route('/unauthorized')
def unauthorized():
    """Halaman 403 — Akses ditolak."""
    return render_template('403.html'), 403


# ============================================================
# HELPER: Redirect berdasarkan role
# ============================================================
def redirect_by_role(role: str):
    """Kembalikan redirect response sesuai role."""
    role_redirects = {
        'hr':         'hr.dashboard',
        'karyawan':   'employee.dashboard',
        'evaluator':  'evaluator.dashboard',
        'management': 'management.dashboard',
    }
    endpoint = role_redirects.get(role, 'auth.login')
    return redirect(url_for(endpoint))
