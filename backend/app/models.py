# backend\app\models.py
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def now_utc():
    return datetime.now(timezone.utc)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    whatsapp = db.Column(db.String(20))
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64))
    role = db.Column(db.String(10), default='user')
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_utc)
    
class Recuerdo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(120))
    story = db.Column(db.Text)
    sede = db.Column(db.String(20))
    year = db.Column(db.String(10))
    filename = db.Column(db.String(255))
    source_type = db.Column(db.String(10))
    source_url = db.Column(db.String(300))
    status = db.Column(db.String(10), default='pendiente')
    created_at = db.Column(db.DateTime, default=now_utc)

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    artist = db.Column(db.String(120))
    album = db.Column(db.String(120))
    sello = db.Column(db.String(120))
    style = db.Column(db.String(60))
    year = db.Column(db.String(10))
    decade = db.Column(db.String(10))
    source_type = db.Column(db.String(10))
    source_url = db.Column(db.String(300))
    filename = db.Column(db.String(255))
    plays = db.Column(db.Integer, default=0)
    status = db.Column(db.String(10), default='pendiente')
    created_at = db.Column(db.DateTime, default=now_utc)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(120), nullable=False)
    year = db.Column(db.String(10))
    decade = db.Column(db.String(10))
    source_type = db.Column(db.String(10))
    source_url = db.Column(db.String(300))
    description = db.Column(db.String(200))
    status = db.Column(db.String(10), default='pendiente')
    created_at = db.Column(db.DateTime, default=now_utc)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=now_utc)
    __table_args__ = (db.UniqueConstraint('user_id', 'track_id'),)

class Listener(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(64), index=True)   # fingerprint del navegador
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    track_id = db.Column(db.Integer)
    last_ping = db.Column(db.DateTime, default=now_utc, index=True)

class Protagonista(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(60))
    name = db.Column(db.String(120), nullable=False)
    meta = db.Column(db.String(120))
    text = db.Column(db.Text)
    quote = db.Column(db.String(300))
    source = db.Column(db.String(120))
    status = db.Column(db.String(10), default='aprobado')
    created_at = db.Column(db.DateTime, default=now_utc)
    media_type = db.Column(db.String(10))
    media_file = db.Column(db.String(200))
    media_url = db.Column(db.String(300))
    
# ---------------------


