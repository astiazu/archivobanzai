# archivobanzai\backend\app\routes_api.py
from flask import Blueprint, jsonify, url_for, request, abort
from .models import db, Recuerdo, Track, Playlist, User, Vote, Listener
from .helpers import current_user, staff, guardar_file
from .config import Config

bp = Blueprint('api', __name__)

def file_url(carpeta, filename):
    return url_for('public.servir_upload', carpeta=carpeta, filename=filename) if filename else None

@bp.get('/api/timeline')
def timeline():
    """Todo el contenido aprobado, ordenado por año. Incluye uploader en tracks."""
    out = []
    for r in Recuerdo.query.filter_by(status='aprobado').all():
        out.append({'cat': 'archivo', 'tipo': r.kind, 'title': r.title, 'story': r.story, 'sede': r.sede,
                    'year': r.year or '',
                    'source': r.source_type or ('file' if r.filename else 'texto'),
                    'url': r.source_url, 'file': file_url('recuerdos', r.filename)})
    for t in Track.query.filter_by(status='aprobado').all():
        u = db.session.get(User, t.user_id)
        out.append({'cat': 'radio', 'tipo': 'track', 'id': t.id, 'title': t.title, 'artist': t.artist, 'style': t.style,
                    'year': t.year or t.decade or '',
                    'source': 'file' if t.filename else t.source_type,
                    'url': t.source_url, 'file': file_url('radio', t.filename),
                    'uploader': u.username if u else 'Desconocido',
                    'uploader_id': t.user_id})
    out.sort(key=lambda i: i.get('year') or '9999')
    return jsonify(out)
    
@bp.get('/api/radio/<year>')
def radio(year):
    """Tracks + listas preparadas de un año o década, con scores y uploader."""
    if year == 'siempre':
        tracks = Track.query.filter_by(status='aprobado').filter(
            db.or_(Track.year == '', Track.year == None)).all()
        lists = Playlist.query.filter_by(status='aprobado').filter(
            db.or_(Playlist.year == '', Playlist.year == None)).all()
    else:
        tracks = Track.query.filter_by(status='aprobado').filter(
            db.or_(Track.year == year, Track.decade == year)).all()
        lists = Playlist.query.filter_by(status='aprobado').filter(
            db.or_(Playlist.year == year, Playlist.decade == year)).all()
    
    tracks_data = []
    for t in tracks:
        score = sum(v.value for v in Vote.query.filter_by(track_id=t.id).all())
        uploader = User.query.get(t.user_id)
        tracks_data.append({
            'id': t.id, 'title': t.title, 'artist': t.artist, 'style': t.style,
            'source': 'file' if t.filename else t.source_type, 'url': t.source_url,
            'file': file_url('radio', t.filename),
            'score': score, 'plays': t.plays or 0,
            'uploader': uploader.username if uploader else 'Desconocido',
            'uploader_id': t.user_id
        })
    
    return jsonify({
        'tracks': tracks_data,
        'playlists': [{'id': p.id, 'title': p.title, 'source_type': p.source_type,
                       'url': p.source_url, 'description': p.description} for p in lists]})

@bp.get('/api/recuerdos')
def recuerdos():
    return jsonify([{'id': r.id, 'kind': r.kind, 'title': r.title, 'story': r.story, 'sede': r.sede,
                     'year': r.year, 'file': file_url('recuerdos', r.filename)}
                    for r in Recuerdo.query.filter_by(status='aprobado').order_by(Recuerdo.year).all()])

@bp.get('/api/tracks')
def tracks():
    return jsonify([{'id': t.id, 'title': t.title, 'artist': t.artist, 'album': t.album, 'sello': t.sello,
                     'style': t.style, 'year': t.year, 'decade': t.decade, 'source_type': t.source_type,
                     'source_url': t.source_url, 'file': file_url('radio', t.filename)}
                    for t in Track.query.filter_by(status='aprobado').all()])

@bp.post('/api/vote/<int:track_id>')
def vote(track_id):
    """Votar pulgar arriba (+1) o abajo (-1). Un voto por usuario."""
    u = current_user()
    if not u or not u.active:
        return jsonify({'error': 'Login requerido'}), 401
    val = request.json.get('value')
    if val not in (1, -1):
        return jsonify({'error': 'Valor inválido'}), 400
    
    existing = Vote.query.filter_by(user_id=u.id, track_id=track_id).first()
    if existing:
        existing.value = val
    else:
        db.session.add(Vote(user_id=u.id, track_id=track_id, value=val))
    db.session.commit()
    
    score = sum(v.value for v in Vote.query.filter_by(track_id=track_id).all())
    return jsonify({'score': score, 'user_vote': val})

@bp.post('/api/play/<int:track_id>')
def play(track_id):
    """Incrementar contador de reproducciones."""
    t = db.session.get(Track, track_id)
    if t:
        t.plays = (t.plays or 0) + 1
        db.session.commit()
    return jsonify({'plays': t.plays if t else 0})

@bp.get('/api/ranking')
def ranking():
    """Top tracks por votos y top aportantes."""
    tracks = Track.query.filter_by(status='aprobado').all()
    scores = {t.id: sum(v.value for v in Vote.query.filter_by(track_id=t.id).all()) for t in tracks}

    top_tracks = sorted(tracks, key=lambda t: (scores[t.id], t.plays or 0), reverse=True)[:5]

    user_scores, user_counts = {}, {}
    for t in tracks:
        u = db.session.get(User, t.user_id)
        if not u: continue
        user_scores[u.username] = user_scores.get(u.username, 0) + scores[t.id]
        user_counts[u.username] = user_counts.get(u.username, 0) + 1
    top_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:5]

    return jsonify({
        'top_tracks': [{'id': t.id, 'title': t.title, 'artist': t.artist,
                        'score': scores[t.id], 'plays': t.plays or 0,
                        'uploader': (db.session.get(User, t.user_id).username if db.session.get(User, t.user_id) else '')}
                       for t in top_tracks],
        'top_users': [{'username': u, 'score': s, 'tracks': user_counts[u]} for u, s in top_users]})

@bp.get('/api/me')
def me():
    """Estado de sesión para el sitio público."""
    u = current_user()
    if u and u.active:
        return jsonify({'logged_in': True, 'username': u.username, 'role': u.role})
    return jsonify({'logged_in': False})

@bp.post('/api/recuerdos')
def api_recuerdos():
    """Subida real de recuerdos desde el sitio público (requiere sesión)."""
    u = current_user()
    if not u or not u.active:
        return jsonify({'error': 'Tenés que estar logueado para subir material.'}), 401

    kind = request.form.get('kind')
    if kind not in Config.ALLOWED and kind != 'historia':
        return jsonify({'error': 'Tipo de recuerdo inválido.'}), 400

    year = (request.form.get('year') or '').strip()
    if year and not (year.isdigit() and 1950 <= int(year) <= 2026):
        return jsonify({'error': 'Año inválido (usá uno entre 1950 y 2026).'}), 400

    title = (request.form.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Poné un título al recuerdo.'}), 400

    source_url = request.form.get('source_url')
    filename, st = None, 'file'
    if kind == 'video' and (source_url or '').startswith('http'):
        st = 'youtube'
    elif kind != 'historia':
        filename = guardar_file(request.files.get('file'), 'recuerdos', Config.ALLOWED[kind])
        if not filename:
            return jsonify({'error': 'Archivo faltante o formato no permitido.'}), 400

    autor = (request.form.get('autor') or '').strip()
    story = (request.form.get('story') or '').strip()
    if autor:
        story = f'Aporte de {autor}. ' + story

    auto = 'aprobado' if staff(u) else 'pendiente'
    db.session.add(Recuerdo(user_id=u.id, kind=kind, title=title, story=story,
                            sede=request.form.get('sede'), year=year,
                            filename=filename, source_type=st, source_url=source_url,
                            status=auto))
    db.session.commit()
    return jsonify({'ok': True, 'status': auto})

@bp.post('/api/listening')
def listening():
    """Heartbeat: el navegador avisa que sigue escuchando. Devuelve stats actuales."""
    import uuid
    from datetime import datetime, timedelta, timezone
    sk = request.cookies.get('bz_sid')
    if not sk:
        sk = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    tid = request.json.get('track_id') if request.is_json else None
    u = current_user()
    db.session.add(Listener(session_key=sk, user_id=(u.id if u else None),
                            track_id=tid, last_ping=now))
    # Purgar pings viejos (más de 2 min)
    cutoff = now - timedelta(seconds=120)
    Listener.query.filter(Listener.last_ping < cutoff).delete()
    db.session.commit()
    # Estadísticas
    activos = Listener.query.filter(Listener.last_ping > now - timedelta(seconds=60))\
                             .with_entities(Listener.session_key).distinct().count()
    comunidad = User.query.filter_by(active=True).count()
    resp = jsonify({'oyentes': activos, 'comunidad': comunidad})
    if not request.cookies.get('bz_sid'):
        resp.set_cookie('bz_sid', sk, max_age=60*60*24*30, httponly=True)
    return resp

@bp.get('/api/stats')
def stats():
    """Stats públicas: oyentes activos + tamaño de la comunidad."""
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    activos = Listener.query.filter(Listener.last_ping > now - timedelta(seconds=60))\
                             .with_entities(Listener.session_key).distinct().count()
    comunidad = User.query.filter_by(active=True).count()
    return jsonify({'oyentes': activos, 'comunidad': comunidad})
