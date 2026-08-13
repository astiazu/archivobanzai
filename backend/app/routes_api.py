# archivobanzai\backend\app\routes_admin.py
from flask import Blueprint, jsonify, url_for
from .models import db, Recuerdo, Track, Playlist

bp = Blueprint('api', __name__)

def file_url(carpeta, filename):
    return url_for('public.servir_upload', carpeta=carpeta, filename=filename) if filename else None

@bp.get('/api/timeline')
def timeline():
    out = []
    for r in Recuerdo.query.filter_by(status='aprobado').all():
        out.append({'cat': 'archivo', 'tipo': r.kind, 'title': r.title, 'story': r.story, 'sede': r.sede,
                    'year': r.year or '',
                    'source': r.source_type or ('file' if r.filename else 'texto'),
                    'url': r.source_url, 'file': file_url('recuerdos', r.filename)})
    for t in Track.query.filter_by(status='aprobado').all():
        out.append({'cat': 'radio', 'tipo': 'track', 'title': t.title, 'artist': t.artist, 'style': t.style,
                    'year': t.year or t.decade or '',
                    'source': 'file' if t.filename else t.source_type,
                    'url': t.source_url, 'file': file_url('radio', t.filename)})
    out.sort(key=lambda i: i.get('year') or '9999')
    return jsonify(out)

@bp.get('/api/radio/<year>')
def radio(year):
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
    return jsonify({
        'tracks': [{'id': t.id, 'title': t.title, 'artist': t.artist, 'style': t.style,
                    'source': 'file' if t.filename else t.source_type, 'url': t.source_url,
                    'file': file_url('radio', t.filename)} for t in tracks],
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