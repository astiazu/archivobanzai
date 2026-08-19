import os
from pathlib import Path

# Cargar .env ANTES de cualquier import de Flask
REPO_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    env_path = REPO_ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)  # override=True para sobreescribir variables viejas
        print(f'>>> .env cargado desde: {env_path}')
    else:
        print(f'>>> AVISO: .env no encontrado en {env_path}')
except ImportError:
    print('>>> AVISO: python-dotenv no instalado. Usá: pip install python-dotenv')

# Ahora sí, imports de Flask
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        db.session.add(User(
            username='admin',
            email='admin@banzai.ar',
            whatsapp='+549000000000',
            password_hash=generate_password_hash(os.environ.get('ADMIN_PASS', 'banzai2026')),
            role='admin', active=True, email_verified=True
        ))
        db.session.commit()
        print('>>> Admin inicial creado')

    from app.seed import run_seed
    run_seed()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=True)