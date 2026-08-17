import os
import re
import shutil
from .models import db, User, Track, Recuerdo
from .config import Config

def _parse_name(filename):
    """'1992 - La Conga - Quique.mp3' -> ('La Conga', '1992', 'Quique')"""
    base = os.path.splitext(filename)[0].replace('_', ' ').strip()
    m = re.match(r'^(\d{4})\s*[-–]\s*(.+)$', base)
    if m:
        resto = m.group(2).split(' - ')
        title = resto[0].strip()
        extra = resto[1].strip() if len(resto) > 1 else ''
        return title, m.group(1), extra
    return base, '', ''

def run_seed():
    """Carga seed/radio y seed/fotos al sitio. Idempotente: no duplica."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    seed_radio = os.path.join(root, 'seed', 'radio')
    seed_fotos = os.path.join(root, 'seed', 'fotos')
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print('>>> Seed: sin admin, salteando')
        return
    added = 0

    if os.path.isdir(seed_radio):
        for f in sorted(os.listdir(seed_radio)):
            if not f.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                continue
            dest = os.path.join(Config.UPLOAD_DIR, 'radio', f)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.exists(dest):
                shutil.copy2(os.path.join(seed_radio, f), dest)
            if not Track.query.filter_by(filename=f).first():
                title, year, artist = _parse_name(f)
                db.session.add(Track(user_id=admin.id, title=title, artist=artist,
                                     year=year, decade=(year[:3] + '0s') if len(year) == 4 else '',
                                     source_type='file', filename=f, status='aprobado'))
                added += 1

    if os.path.isdir(seed_fotos):
        for f in sorted(os.listdir(seed_fotos)):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue
            dest = os.path.join(Config.UPLOAD_DIR, 'recuerdos', f)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if not os.path.exists(dest):
                shutil.copy2(os.path.join(seed_fotos, f), dest)
            if not Recuerdo.query.filter_by(filename=f).first():
                title, year, _ = _parse_name(f)
                db.session.add(Recuerdo(user_id=admin.id, kind='foto', title=title,
                                        sede='ambas', year=year, filename=f,
                                        source_type='file', status='aprobado'))
                added += 1

    db.session.commit()
    print(f'>>> Seed: {added} elementos nuevos cargados')