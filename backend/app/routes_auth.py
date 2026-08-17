import os
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from flask import (Blueprint, render_template, request, redirect, url_for, session, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Recuerdo, Track, Playlist
from .helpers import current_user, staff, login_required, guardar_file
from .config import Config

bp = Blueprint('auth', __name__)

# CREDENCIALES HARDCODEADAS (desarrollo local)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'in-v3.mailjet.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USER = os.environ.get('EMAIL_USER', '62ec24390d5c498f170c85f5991e4637')
EMAIL_PASS = os.environ.get('EMAIL_PASS', '856c818fa165b4e5c9fd9ee11b4dced9')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'banzaishow.minaclavero@gmail.com')

def valid_year(y):
    return bool(y) and y.isdigit() and 1950 <= int(y) <= 2026

def validar_email(e):
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', (e or '').strip()))

def validar_whatsapp(w):
    digits = re.sub(r'[^\d]', '', w or '')
    return 10 <= len(digits) <= 15

def normalizar_whatsapp(w):
    w = (w or '').strip()
    digits = re.sub(r'[^\d]', '', w)
    return ('+' + digits) if w.startswith('+') else digits

def enviar_mail_verificacion(u):
    """Manda el link de confirmación por Mailjet."""
    link = url_for('auth.verificar', token=u.verification_token, _external=True)
    cuerpo = (f'Hola {u.username},\n\n'
              f'Confirmá tu mail para activar tu cuenta en Archivo Ban Zai:\n{link}\n\n'
              f'Si no fuiste vos, ignorá este mail.')
    msg = MIMEText(cuerpo)
    msg['Subject'] = 'Confirmá tu cuenta - Archivo Ban Zai'
    msg['From'] = f'Archivo Ban Zai <{EMAIL_FROM}>'
    msg['To'] = u.email
    
    print(f'>>> [DEBUG] Enviando mail a {u.email} vía {EMAIL_HOST}')
    print(f'>>> [DEBUG] User: {EMAIL_USER[:8]}...')
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as s:
            s.starttls()
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        print(f'>>> ✅ Mail enviado a {u.email}')
        return True
    except Exception as e:
        print(f'>>> ❌ Error enviando mail: {e}')
        return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.active and check_password_hash(u.password_hash, request.form['password']):
            session.update(user_id=u.id, username=u.username, role=u.role)
            flash(f'¡Bienvenido, {u.username}!')
            return redirect(url_for('admin.panel') if u.role == 'admin' else url_for('auth.subir'))
        if u and not u.active and not u.email_verified:
            flash('Tu cuenta todavía no está verificada. Buscá el mail de confirmación (revisá la carpeta SPAM / Correo no deseado) y tocá el link.')
        else:
            flash('Usuario o contraseña inválidos (o cuenta sin activar).')
    return render_template('login.html')

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        whatsapp = (request.form.get('whatsapp') or '').strip()
        password = request.form.get('password') or ''

        if len(username) < 3:
            flash('El usuario debe tener al menos 3 caracteres.')
        elif not validar_email(email):
            flash('Email inválido. Usá un mail real (ej.: nombre@gmail.com).')
        elif not validar_whatsapp(whatsapp):
            flash('WhatsApp inválido. Ej.: +54 9 351 555-5555 (entre 10 y 15 dígitos).')
        elif len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.')
        elif User.query.filter_by(username=username).first():
            flash('Ese usuario ya existe.')
        elif User.query.filter_by(email=email).first():
            flash('Ese email ya está registrado.')
        else:
            u = User(username=username, email=email, whatsapp=normalizar_whatsapp(whatsapp),
                     password_hash=generate_password_hash(password),
                     verification_token=secrets.token_urlsafe(32))
            db.session.add(u)
            db.session.commit()
            enviado = enviar_mail_verificacion(u)
            flash('Cuenta creada. Te mandamos un mail con el link de confirmación.'
                  if enviado else 'Cuenta creada. Error al enviar el mail, contactá al admin.')
            return redirect(url_for('auth.login'))
    return render_template('registro.html')

@bp.route('/verificar/<token>')
def verificar(token):
    u = User.query.filter_by(verification_token=token).first()
    if not u:
        flash('Link inválido o ya usado.')
        return redirect(url_for('auth.login'))
    u.email_verified = True
    u.active = True
    u.verification_token = None
    db.session.commit()
    flash(f'¡Mail confirmado, {u.username}! Ya podés entrar y votar.')
    return redirect(url_for('auth.login'))

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