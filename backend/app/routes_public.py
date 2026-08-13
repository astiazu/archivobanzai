# archivobanzai\backend\app\routes_public.py
import os
from flask import Blueprint, send_from_directory, abort
from .config import Config

bp = Blueprint('public', __name__)

@bp.route('/')
def index():
    return send_from_directory(Config.FRONT_DIR, 'index.html')

@bp.route('/uploads/<carpeta>/<path:filename>')
def servir_upload(carpeta, filename):
    if carpeta not in ('recuerdos', 'radio'): abort(404)
    return send_from_directory(os.path.join(Config.UPLOAD_DIR, carpeta), filename)