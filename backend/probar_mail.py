import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from pathlib import Path

# Buscar .env en el repo (sube desde backend/ hasta la raíz)
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_CANDIDATES = [SCRIPT_DIR / '.env', SCRIPT_DIR.parent / '.env']
for p in ENV_CANDIDATES:
    if p.exists():
        load_dotenv(p)
        print('>>> Usando .env desde:', p)
        break

HOST = os.environ.get('EMAIL_HOST')
PORT = int(os.environ.get('EMAIL_PORT', '0') or '0')
USER = os.environ.get('EMAIL_USER')
PASS = os.environ.get('EMAIL_PASS')
FROM = os.environ.get('EMAIL_FROM', USER)

print(f'Host: {HOST}')
print(f'Port: {PORT}')
print(f'User: {USER[:8]}...' if USER else 'User: None')

if not all([HOST, PORT, USER, PASS]):
    print('❌ Faltan variables. Revisá el .env')
    exit()

msg = MIMEText('Esto es una prueba desde Archivo Ban Zai.')
msg['Subject'] = 'Prueba SMTP - Ban Zai'
msg['From'] = f'Archivo Ban Zai <{FROM}>'
msg['To'] = 'tu-propio-mail@gmail.com'   # ← poné un mail tuyo para recibir

try:
    with smtplib.SMTP(HOST, PORT) as s:
        s.starttls()
        s.login(USER, PASS)
        s.send_message(msg)
    print('✅ Mail enviado OK — revisá tu bandeja de entrada')
except Exception as e:
    print('❌ Error:', e)