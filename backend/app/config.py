# archivobanzai\backend\app\config.py
import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))  # backend/
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))               # raíz repo

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-banzai-2026-cambiar-en-produccion')
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'banzai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024          # 200 MB por archivo
    FRONT_DIR = os.path.join(ROOT_DIR, 'frontend')  # sitio público
    UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')  # archivos de usuarios
    ALLOWED = {
        'foto':  {'png','jpg','jpeg','webp','gif'},
        'flyer': {'png','jpg','jpeg','webp','pdf'},
        'audio': {'mp3','wav','m4a','ogg'},
        'video': {'mp4','mov','webm'},
        'radio': {'mp3','wav','m4a','ogg'},
    }