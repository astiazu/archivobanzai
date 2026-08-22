import os
import re
import shutil
import json
from .models import db, User, Track, Recuerdo, Protagonista
from .config import Config

PROTAGONISTAS = [
    {'role': 'DJ · SALDÁN', 'name': 'Eduardo Quintana', 'meta': 'BARRIO PUEYRREDÓN · HOY EN ALEMANIA',
     'text': 'Trabajó como DJ en Ban Zai Saldán. Hoy regentea un restaurante en Alemania, pero recuerda con cariño sus inicios en la disco mítica de Av. Latinoamérica.',
     'quote': 'Hacía divertir mucho a la gente.', 'source': 'FUENTE · Cadena 3 ↗'},
    {'role': 'RADIO · MINA CLAVERO', 'name': 'FM 104.9 Rockhola', 'meta': 'GRUPO FUNDADOR · DESDE 1986',
     'text': 'El mismo grupo que en 1986 hacía locución en la Playa de Ban Zai y armó una radio al aire libre, hoy sostiene FM 104.9 Rockhola y Radio Portneuf Club.',
     'quote': 'Disfrutando de la magia de la música, de los grandes locutores, nos volvimos adictos a la buena música.', 'source': 'FUENTE · App Rockhola ↗'},
    {'role': 'DUEÑO · HOY', 'name': 'Quique', 'meta': 'BAN ZAI SHOW · REAPERTURA 2026',
     'text': 'Detrás del regreso de Ban Zai Mina Clavero en septiembre de 2026. Lidera Ban Zai Show y la reconstrucción de la marca como archivo vivo de la noche cordobesa.',
     'quote': 'Pronto, un testimonio del propio Quique sobre cómo empezó este regreso.', 'source': ' TESTIMONIO EN CURSO'},
    {'role': 'LA GENTE', 'name': 'Vos, que estuviste ahí', 'meta': 'CADA NOCHE · CADA VERANO',
     'text': 'Esta ficha queda vacía a propósito. Porque el archivo se completa con cada foto, cada testimonio, cada recuerdo que nos mandes.',
     'quote': '¿Estuviste vos? Entonces tu lugar en el archivo está esperándote.', 'source': ''},
         {'role': 'BARMAN · MINA CLAVERO', 'name': 'El Turco Hassan', 'meta': '18 TEMPORADAS DETRÁS DE LA BARRA',
     'text': 'Dicen que el Turco servía un vaso por segundo en la terraza de Playa Central y que conocía el trago favorito de cada habitué. La barra era el corazón de la noche, repite hasta hoy.',
     'quote': 'La barra era el corazón de la noche.', 'source': '🟡 HISTORIA QUE SE CUENTA'},
    {'role': 'LOCUTOR · PLAYA 86', 'name': 'El Negro Aguirre', 'meta': 'LA VOZ DE LA RADIO EN LA PLAYA',
     'text': 'En el verano del 86 puso la voz a la radio al aire libre que el grupo de amigos armó en la Playa de Ban Zai. Los que estuvieron dicen que su saludo se escuchaba hasta del otro lado del río.',
     'quote': '¡Buenas tardes, Mina Clavero!', 'source': '🟡 HISTORIA QUE SE CUENTA'},
    {'role': 'FOTÓGRAFA · AÑOS 90', 'name': 'Marta Gutiérrez', 'meta': 'RETRATÓ LOS VERANOS DEL 90 AL 98',
     'text': 'Recorría la pista con una camarita de flash cuadrado vendiendo fotos a dos pesos. Miles de cordobeses tienen todavía su foto en una billetera o un álbum familiar. El archivo quiere encontrarlas.',
     'quote': 'Cada foto era un pedacito de noche que la gente se llevaba a casa.', 'source': '🟡 EN BÚSQUEDA DE SUS FOTOS'},
]

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

def seed_protagonistas_folder():
    """Carga seed/protagonistas/: pares Nombre.json + Nombre.(jpg|mp3|mp4)."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    carpeta = os.path.join(root, 'seed', 'protagonistas')
    if not os.path.isdir(carpeta):
        return 0
    exts = ('jpg', 'jpeg', 'png', 'webp', 'gif', 'mp4', 'mov', 'webm', 'mp3', 'wav', 'm4a', 'ogg')
    added = 0
    for f in sorted(os.listdir(carpeta)):
        if not f.lower().endswith('.json'):
            continue
        base = os.path.splitext(f)[0]
        with open(os.path.join(carpeta, f), encoding='utf-8') as fh:
            data = json.load(fh)
        name = data.get('name', base)
        if Protagonista.query.filter_by(name=name).first():
            continue
        media_file, media_type = None, ''
        for ext in exts:
            cand = os.path.join(carpeta, base + '.' + ext)
            if os.path.exists(cand):
                dest = os.path.join(Config.UPLOAD_DIR, 'protagonistas', base + '.' + ext)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if not os.path.exists(dest):
                    shutil.copy2(cand, dest)
                media_file = base + '.' + ext
                media_type = 'foto' if ext in ('jpg', 'jpeg', 'png', 'webp', 'gif') else 'video' if ext in ('mp4', 'mov', 'webm') else 'audio'
                break
        db.session.add(Protagonista(
            role=data.get('role', ''), name=name, meta=data.get('meta', ''),
            text=data.get('text', ''), quote=data.get('quote', ''),
            source=data.get('source', ''), media_type=media_type,
            media_file=media_file, media_url=data.get('media_url', ''),
            status='aprobado'))
        added += 1
    return added

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

    for p in PROTAGONISTAS:
        if not Protagonista.query.filter_by(name=p['name']).first():
            db.session.add(Protagonista(**p))

    added += seed_protagonistas_folder()

    db.session.commit()
    print(f'>>> Seed: {added} elementos nuevos cargados')