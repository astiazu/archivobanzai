# archivobanzai\backend\app\helpers.py
import os, secrets
from functools import wraps
from flask import session, redirect, url_for
from .config import Config
from .models import db, User

def current_user():
    return db.session.get(User, session['user_id']) if 'user_id' in session else None

def staff(u):
    return u is not None and u.role in ('admin', 'editor')

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u or not u.active: return redirect(url_for('auth.login'))
        return f(*a, **k)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u or not u.active or u.role != 'admin': return redirect(url_for('auth.login'))
        return f(*a, **k)
    return w

def guardar_file(f, carpeta, exts):
    if not f or not f.filename or '.' not in f.filename: return None
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in exts: return None
    name = f"{secrets.token_hex(6)}.{ext}"
    f.save(os.path.join(Config.UPLOAD_DIR, carpeta, name))
    return name