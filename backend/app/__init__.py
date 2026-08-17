# \banzai\archivobanzai\backend\app\__init__.py
import os
from flask import Flask
from .config import Config
from .models import db

def create_app():
    app = Flask(__name__, static_folder=Config.FRONT_DIR, static_url_path='')
    app.config.from_object(Config)

    os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_DIR, 'recuerdos'), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_DIR, 'radio'), exist_ok=True)

    db.init_app(app)

    from .routes_public import bp as public_bp
    from .routes_auth import bp as auth_bp
    from .routes_admin import bp as admin_bp
    from .routes_api import bp as api_bp
    from .admin_users import bp as admin_users_bp

 
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_users_bp)

    @app.after_request
    def cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    return app