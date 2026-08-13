# archivobanzai\backend\run.py
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        db.session.add(User(username='admin', email='admin@banzai.ar',
                            password_hash=generate_password_hash('banzai2026'),
                            role='admin', active=True))
        db.session.commit()
        print('>>> Admin inicial: admin / banzai2026')

if __name__ == '__main__':
    app.run(debug=True, port=5000)