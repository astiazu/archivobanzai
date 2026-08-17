# archivobanzai\backend\app\admin_user.py
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import db, User, Vote, Track, Recuerdo, Playlist
from .helpers import current_user
from .routes_auth import enviar_mail_verificacion

bp = Blueprint('admin_users', __name__)

def _admin():
    u = current_user()
    return u if (u and u.role == 'admin') else None

@bp.route('/admin/usuarios')
def usuarios():
    admin = _admin()
    if not admin:
        flash('Solo el administrador puede gestionar usuarios.')
        return redirect(url_for('auth.login'))
    usuarios = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', usuarios=usuarios, admin=admin)

@bp.route('/admin/usuarios/<int:uid>/editar', methods=['POST'])
def editar(uid):
    admin = _admin()
    if not admin: return redirect(url_for('auth.login'))
    u = db.session.get(User, uid)
    if not u:
        flash('Usuario inexistente.')
        return redirect(url_for('admin_users.usuarios'))

    nuevo_user = (request.form.get('username') or '').strip()
    nuevo_email = (request.form.get('email') or '').strip().lower()
    nuevo_wp = (request.form.get('whatsapp') or '').strip()
    nuevo_rol = request.form.get('role')

    if nuevo_user and nuevo_user != u.username:
        if User.query.filter_by(username=nuevo_user).first():
            flash('Ese nombre de usuario ya existe.')
            return redirect(url_for('admin_users.usuarios'))
        u.username = nuevo_user

    if nuevo_email and nuevo_email != u.email:
        if User.query.filter_by(email=nuevo_email).first():
            flash('Ese email ya está usado por otro usuario.')
            return redirect(url_for('admin_users.usuarios'))
        u.email = nuevo_email
        u.email_verified = False
        u.verification_token = secrets.token_urlsafe(32)

    if nuevo_wp:
        u.whatsapp = nuevo_wp

    if nuevo_rol in ('user', 'editor', 'admin'):
        if u.id == admin.id and nuevo_rol != 'admin':
            flash('No podés quitarte el rol de admin a vos mismo.')
        else:
            u.role = nuevo_rol

    db.session.commit()
    flash(f'Usuario {u.username} actualizado.')
    return redirect(url_for('admin_users.usuarios'))

@bp.route('/admin/usuarios/<int:uid>/toggle', methods=['POST'])
def toggle(uid):
    admin = _admin()
    if not admin: return redirect(url_for('auth.login'))
    u = db.session.get(User, uid)
    if not u:
        return redirect(url_for('admin_users.usuarios'))
    if u.id == admin.id:
        flash('No podés suspenderte a vos mismo.')
    else:
        u.active = not u.active
        db.session.commit()
        flash(f'{u.username} ahora está {"ACTIVO" if u.active else "SUSPENDIDO"}.')
    return redirect(url_for('admin_users.usuarios'))

@bp.route('/admin/usuarios/<int:uid>/reenviar', methods=['POST'])
def reenviar(uid):
    admin = _admin()
    if not admin: return redirect(url_for('auth.login'))
    u = db.session.get(User, uid)
    if not u:
        return redirect(url_for('admin_users.usuarios'))
    if u.email_verified:
        flash(f'{u.username} ya tiene el mail verificado.')
    else:
        if not u.verification_token:
            u.verification_token = secrets.token_urlsafe(32)
            db.session.commit()
        enviar_mail_verificacion(u)
        flash(f'Mail de verificación reenviado a {u.email} (revisar SPAM).')
    return redirect(url_for('admin_users.usuarios'))

@bp.route('/admin/usuarios/<int:uid>/eliminar', methods=['POST'])
def eliminar(uid):
    admin = _admin()
    if not admin: return redirect(url_for('auth.login'))
    u = db.session.get(User, uid)
    if not u:
        return redirect(url_for('admin_users.usuarios'))
    if u.id == admin.id:
        flash('No podés eliminar tu propia cuenta de admin.')
    else:
        # El archivo no se pierde: el contenido pasa al admin
        Vote.query.filter_by(user_id=uid).delete()
        Track.query.filter_by(user_id=uid).update({'user_id': admin.id})
        Recuerdo.query.filter_by(user_id=uid).update({'user_id': admin.id})
        Playlist.query.filter_by(user_id=uid).update({'user_id': admin.id})
        nombre = u.username
        db.session.delete(u)
        db.session.commit()
        flash(f'Usuario {nombre} eliminado. Su contenido pasó al admin para no perder el archivo.')
    return redirect(url_for('admin_users.usuarios'))

