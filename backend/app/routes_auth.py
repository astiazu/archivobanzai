# archivobanzai\backend\app\routes_auth.py
from flask import (Blueprint, render_template, request, redirect, url_for, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Recuerdo, Track, Playlist
from .helpers import current_user, staff, login_required, guardar_file
from .config import Config

bp = Blueprint('auth', __name__)

def valid_year(y):
    return bool(y) and y.isdigit() and 1950 <= int(y) <= 2026

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.active and check_password_hash(u.password_hash, request.form['password']):
            session.update(user_id=u.id, username=u.username, role=u.role)
            flash(f'¡Bienvenido, {u.username}!')
            return redirect(url_for('admin.panel') if u.role == 'admin' else url_for('auth.subir'))
        flash('Usuario o contraseña inválidos (o cuenta sin activar).')
    return render_template('login.html')

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Ese usuario ya existe.')
        else:
            db.session.add(User(username=request.form['username'], email=request.form['email'],
                                password_hash=generate_password_hash(request.form['password'])))
            db.session.commit()
            flash('Cuenta creada. Queda pendiente de activación por un administrador.')
            return redirect(url_for('auth.login'))
    return render_template('registro.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/subir', methods=['GET', 'POST'])
@login_required
def subir():
    u = current_user()
    if request.method == 'POST':
        destino = request.form.get('destino')
        auto = 'aprobado' if staff(u) else 'pendiente'
        year = request.form.get('year') or ''
        if year and not valid_year(year):
            flash('Año inválido (usá un año entre 1950 y 2026).'); return redirect(url_for('auth.subir'))
        if destino == 'archivo':
            kind = request.form.get('kind')
            if kind not in Config.ALLOWED and kind != 'historia':
                flash('Tipo de recuerdo inválido.'); return redirect(url_for('auth.subir'))
            filename, source_url = None, request.form.get('source_url')
            if kind == 'video' and source_url:
                st = 'youtube'
            else:
                st = 'file'
                if kind != 'historia':
                    filename = guardar_file(request.files.get('file'), 'recuerdos', Config.ALLOWED[kind])
                    if not filename:
                        flash('Archivo faltante o formato no permitido.'); return redirect(url_for('auth.subir'))
            db.session.add(Recuerdo(user_id=u.id, kind=kind, title=request.form.get('title'),
                                    story=request.form.get('story'), sede=request.form.get('sede'),
                                    year=year, filename=filename, source_type=st, source_url=source_url, status=auto))
            flash('Recuerdo ' + ('publicado.' if auto == 'aprobado' else 'enviado a moderación.'))
        elif destino == 'radio':
            if not request.form.get('title'):
                flash('El track necesita un título.'); return redirect(url_for('auth.subir'))
            source_type = request.form.get('source_type')
            filename, source_url = None, request.form.get('source_url')
            if source_type in ('youtube', 'spotify') and not (source_url or '').startswith('http'):
                flash('Pegá una URL válida de YouTube/Spotify (debe empezar con http).')
                return redirect(url_for('auth.subir'))
            if source_type == 'file':
                filename = guardar_file(request.files.get('file'), 'radio', Config.ALLOWED['radio'])
                if not filename:
                    flash('Formato no permitido en la RADIO (solo mp3/wav/m4a/ogg). Si es un VIDEO (.mp4/.mov/.webm), subilo desde el formulario de arriba con tipo "Video".')
                    return redirect(url_for('auth.subir'))
            db.session.add(Track(user_id=u.id, title=request.form.get('title'), artist=request.form.get('artist'),
                                 album=request.form.get('album'), sello=request.form.get('sello'),
                                 style=request.form.get('style'), year=year,
                                 decade=(year[:3] + '0s') if len(year) == 4 else '',
                                 source_type=source_type, source_url=source_url, filename=filename, status=auto))
            flash('Track ' + ('publicado.' if auto == 'aprobado' else 'enviado a moderación.'))
        elif destino == 'playlist':
            if not staff(u):
                flash('Solo editores o administradores pueden crear listas.'); return redirect(url_for('auth.subir'))
            db.session.add(Playlist(user_id=u.id, title=request.form.get('title'), year=year,
                                    decade=(year[:3] + '0s') if len(year) == 4 else '',
                                    source_type=request.form.get('source_type'), source_url=request.form.get('source_url'),
                                    description=request.form.get('description'), status='aprobado'))
            flash('Lista preparada y publicada.')
        db.session.commit()
        return redirect(url_for('auth.subir'))
    return render_template('subir.html', es_staff=staff(u))