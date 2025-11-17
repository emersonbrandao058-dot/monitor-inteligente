import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Variáveis
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA_APP = os.getenv("EMAIL_SENHA_APP")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

# Telegram
def enviar_telegram(mensagem: str) -> bool:
    try:
        if not BOT_TOKEN or not CHAT_ID:
            return False
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensagem}
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200
    except:
        return False

# Email
def enviar_email(assunto: str, mensagem: str) -> bool:
    try:
        if not EMAIL_REMETENTE or not EMAIL_SENHA_APP or not EMAIL_DESTINO:
            return False
        msg = MIMEText(mensagem)
        msg["Subject"] = assunto
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
            smtp.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            smtp.send_message(msg)
        return True
    except:
        return False

def montar_mensagem(cpu_val: float, mem_val: float) -> str:
    tempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"⚠️ ALERTA DO MONITOR\n"
        f"Horário: {tempo}\n"
        f"CPU: {cpu_val:.1f}%\n"
        f"Memória: {mem_val:.1f}%"
    )
