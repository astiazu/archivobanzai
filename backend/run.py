import os
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        db.session.add(User(username='admin', email='admin@banzai.ar',
                            password_hash=generate_password_hash(os.environ.get('ADMIN_PASS', 'banzai2026')),
                            role='admin', active=True))
        db.session.commit()
        print('>>> Admin inicial creado')

if __name__ == '__main__':
    # En local: puerto 5000 con debug. En Render: usa $PORT y sin debug.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=('PORT' not in os.environ))