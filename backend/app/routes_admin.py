# archivobanzai\backend\app\routes_admin.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .models import db, User, Recuerdo, Track, Playlist
from .helpers import current_user, admin_required
from .config import Config

bp = Blueprint('admin', __name__)
MODELOS = {'recuerdo': Recuerdo, 'track': Track, 'playlist': Playlist}

@bp.route('/panel')
def panel():
    u = current_user()
    if not u or not u.active: return redirect(url_for('auth.login'))
    if u.role != 'admin':
        flash('No tenés permisos para acceder al panel.'); return redirect(url_for('public.index'))
    return render_template('panel.html',
        usuarios=User.query.filter_by(active=False).all(),
        rec_pend=Recuerdo.query.filter_by(status='pendiente').order_by(Recuerdo.created_at).all(),
        tra_pend=Track.query.filter_by(status='pendiente').order_by(Track.created_at).all(),
        lis_pend=Playlist.query.filter_by(status='pendiente').all(),
        aprobados=Recuerdo.query.filter_by(status='aprobado').order_by(Recuerdo.created_at.desc()).limit(20).all(),
        tracks_ok=Track.query.filter_by(status='aprobado').order_by(Track.created_at.desc()).limit(20).all(),
        lists_ok=Playlist.query.filter_by(status='aprobado').order_by(Playlist.created_at.desc()).all())

@bp.post('/panel/accion/<tipo>/<int:id>')
@admin_required
def panel_accion(tipo, id):
    Model = MODELOS.get(tipo) or abort(404)
    item = db.session.get(Model, id) or abort(404)
    acc = request.form.get('action')
    if acc == 'aprobar': item.status = 'aprobado'
    elif acc == 'rechazar': item.status = 'rechazado'
    elif acc == 'eliminar':
        fn = getattr(item, 'filename', None)
        if fn:
            p = os.path.join(Config.UPLOAD_DIR, 'recuerdos' if tipo == 'recuerdo' else 'radio', fn)
            if os.path.exists(p): os.remove(p)
        db.session.delete(item)
    db.session.commit()
    return redirect(url_for('admin.panel'))

@bp.post('/panel/usuario/<int:id>')
@admin_required
def panel_usuario(id):
    u = db.session.get(User, id) or abort(404)
    acc = request.form.get('action')
    if acc == 'activar': u.active = True
    elif acc == 'suspender': u.active = False
    elif acc == 'hacer_editor': u.role = 'editor'
    elif acc == 'hacer_admin': u.role = 'admin'
    db.session.commit()
    return redirect(url_for('admin.panel'))

@bp.route('/panel/editar/<tipo>/<int:id>', methods=['GET', 'POST'])
@admin_required
def panel_editar(tipo, id):
    Model = MODELOS.get(tipo) or abort(404)
    item = db.session.get(Model, id) or abort(404)
    if request.method == 'POST':
        f = request.form
        item.title = f.get('title') or item.title
        item.year = f.get('year') or item.year
        item.status = f.get('status') or item.status
        if tipo == 'recuerdo':
            item.sede = f.get('sede') or item.sede
            item.story = f.get('story') or item.story
        elif tipo == 'track':
            item.artist = f.get('artist') or item.artist
            item.album = f.get('album') or item.album
            item.sello = f.get('sello') or item.sello
            item.style = f.get('style') or item.style
        db.session.commit()
        flash('Cambios guardados.')
        return redirect(url_for('admin.panel'))
    return render_template('editar.html', item=item, tipo=tipo)