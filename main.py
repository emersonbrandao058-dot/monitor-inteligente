# main.py -- Versão final otimizada
# ==========================================
# MONITOR DE SISTEMA VISUAL - PEI
# Autor: Bruno Brandão (refatorado)
# ==========================================

import streamlit as st
import pandas as pd
import psutil
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
import mysql.connector
from mysql.connector import Error
from hashlib import sha256
import os
from dotenv import load_dotenv
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets

# -------------------------
# Configurações e variáveis de ambiente
# -------------------------
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "monitor")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "")
EMAIL_SENHA_APP = os.getenv("EMAIL_SENHA_APP", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

CPU_LIMITE = 80
MEMORIA_LIMITE = 80
INTERVALO = 2  # segundos

# -------------------------
# Conexão com banco de dados
# -------------------------
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

# -------------------------
# Envio de alertas
# -------------------------
def enviar_email(destinatario: str, assunto: str, corpo_html: str) -> bool:
    if not EMAIL_REMETENTE or not EMAIL_SENHA_APP:
        st.warning("E-mail do sistema não configurado no .env")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo_html, 'html'))
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")
        return False

def enviar_telegram(mensagem: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram não configurado no .env")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Erro ao enviar Telegram: {e}")
        return False

# -------------------------
# Segurança / usuário
# -------------------------
def hash_senha(senha: str) -> str:
    return sha256(senha.encode()).hexdigest()

def registrar_usuario_db(nome: str, email: str, senha: str, telegram_id: str="") -> (bool, str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, telegram_id) VALUES (%s,%s,%s,%s)",
            (nome, email, hash_senha(senha), telegram_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, "Usuário registrado."
    except Error as e:
        return False, str(e)

def autenticar_usuario_db(email: str, senha: str) -> (bool, str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM usuarios WHERE email=%s AND senha_hash=%s", (email, hash_senha(senha)))
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            return True, r[1]
        return False, ""
    except Error:
        return False, ""

# -------------------------
# Estado da sessão
# -------------------------
def init_session_state():
    if "historico_cpu" not in st.session_state:
        st.session_state.historico_cpu = []
        st.session_state.historico_memoria = []
        st.session_state.historico_tempo = []
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = False
        st.session_state.usuario_nome = ""
        st.session_state.usuario_email = ""
    if "alertas_historico" not in st.session_state:
        st.session_state.alertas_historico = []
    if "test_alert_retry" not in st.session_state:
        st.session_state.test_alert_retry = {"attempts_left": 0, "cooldown_until": None, "last_target": ""}

init_session_state()

def atualizar_historico(cpu, memoria):
    tempo = datetime.now().strftime("%H:%M:%S")
    st.session_state.historico_cpu.append(cpu)
    st.session_state.historico_memoria.append(memoria)
    st.session_state.historico_tempo.append(tempo)
    if len(st.session_state.historico_cpu) > 60:
        st.session_state.historico_cpu.pop(0)
        st.session_state.historico_memoria.pop(0)
        st.session_state.historico_tempo.pop(0)
    return pd.DataFrame({
        "Tempo": st.session_state.historico_tempo,
        "CPU (%)": st.session_state.historico_cpu,
        "Memória (%)": st.session_state.historico_memoria
    }).set_index("Tempo")

# -------------------------
# Menu lateral
# -------------------------
menu = st.sidebar.selectbox("Menu", ["Monitor Inteligente", "Login/Registro", "Instruções"])

# -------------------------
# Instruções
# -------------------------
if menu == "Instruções":
    st.title("📖 Como iniciar o projeto no VS Code")
    st.markdown(r"""
    ### Passo 1: Abrir o projeto
    - Abra o Visual Studio Code.
    - Vá em `Arquivo > Abrir Pasta`.
    - Selecione a pasta do projeto.

    ### Passo 2: Criar e ativar ambiente virtual
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```

    ### Passo 3: Instalar dependências
    ```powershell
    pip install -r requirements.txt
    ```

    ### Passo 4: Rodar o monitor
    ```powershell
    streamlit run main.py
    ```

    ### Passo 5: Acessar o monitor
    - Abra o navegador e vá para `http://localhost:8502`
    """, unsafe_allow_html=True)

# -------------------------
# Login / Registro / Recuperar senha
# -------------------------
elif menu == "Login/Registro":
    st.title("🔑 Registrar / Entrar")
    st.subheader("Crie sua conta ou faça login")
    aba = st.radio("O que deseja fazer?", ["Entrar", "Registrar Usuário", "Recuperar senha"])

    if aba == "Registrar Usuário":
        nome = st.text_input("Nome completo", key="r_nome")
        email = st.text_input("E-mail", key="r_email")
        senha = st.text_input("Senha", type="password", key="r_senha")
        telegram_id = st.text_input("Telegram ID (opcional)", key="r_telegram")
        if st.button("Cadastrar"):
            if not (nome and email and senha):
                st.warning("Preencha todos os campos obrigatórios.")
            else:
                ok, msg = registrar_usuario_db(nome, email, senha, telegram_id)
                if ok:
                    st.success("✅ " + msg)
                    st.session_state.usuario_logado = True
                    st.session_state.usuario_nome = nome
                    st.session_state.usuario_email = email
                    st.info("Você foi logado automaticamente.")
                    corpo = f"""<html><body>
                               <h2>Bem-vindo ao Monitor Inteligente</h2>
                               <p>Olá {nome}, seu cadastro foi realizado com sucesso!</p>
                               <p>E-mail enviado para: <b>{email}</b></p>
                               </body></html>"""
                    enviar_email(email, "Bem-vindo ao Monitor Inteligente", corpo)
                    if telegram_id:
                        enviar_telegram(f"Olá {nome}, seu cadastro foi realizado com sucesso!")
                else:
                    st.error("❌ Erro: " + msg)

    elif aba == "Entrar":
        email = st.text_input("E-mail", key="l_email")
        senha = st.text_input("Senha", type="password", key="l_senha")
        if st.button("Entrar"):
            ok, nome = autenticar_usuario_db(email, senha)
            if ok:
                st.success(f"🎉 Bem-vindo(a), {nome}!")
                st.session_state.usuario_logado = True
                st.session_state.usuario_nome = nome
                st.session_state.usuario_email = email
            else:
                st.error("E-mail ou senha incorretos.")

    elif aba == "Recuperar senha":
        email_rc = st.text_input("Digite seu e-mail cadastrado", key="rec_email")
        if st.button("Recuperar senha (enviar senha temporária)"):
            if not email_rc:
                st.warning("Informe o e-mail.")
            else:
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT nome FROM usuarios WHERE email=%s", (email_rc,))
                    r = cur.fetchone()
                    cur.close()
                    conn.close()
                    if r:
                        nome_usr = r[0]
                        senha_temp = secrets.token_urlsafe(6)
                        senha_hash = hash_senha(senha_temp)
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE usuarios SET senha_hash=%s WHERE email=%s", (senha_hash, email_rc))
                        conn.commit()
                        cur.close()
                        conn.close()
                        corpo_html = f"""
                        <html><body>
                        <h2>Recuperação de Senha</h2>
                        <p>Olá {nome_usr}, sua senha temporária é: <b>{senha_temp}</b></p>
                        <p>Altere a senha após o login.</p>
                        </body></html>
                        """
                        ok_mail = enviar_email(email_rc, "Recuperação de Senha - Monitor Inteligente", corpo_html)
                        if ok_mail:
                            st.success("Senha temporária enviada por e-mail.")
                        else:
                            st.error("Falha ao enviar e-mail. Verifique configuração do .env.")
                    else:
                        st.error("E-mail não cadastrado.")
                except Exception as e:
                    st.error("Erro ao processar solicitação.")

# -------------------------
# Monitor Inteligente
# -------------------------
elif menu == "Monitor Inteligente":
    st.set_page_config(page_title="Monitor Inteligente", layout="wide")
    st.markdown(r"""<h1 style='text-align:center; color:white;'>🧠 Monitor Inteligente de Sistema</h1>""", unsafe_allow_html=True)
    st_autorefresh(interval=INTERVALO * 1000, key="auto_refresh_monitor")

    colh1, colh2 = st.columns([3,1])
    with colh1:
        st.markdown("#### Dashboard em tempo real")
    with colh2:
        if st.session_state.usuario_logado:
            st.markdown(f"**Usuário:** {st.session_state.usuario_nome}")
            if st.button("Sair"):
                st.session_state.usuario_logado = False
                st.session_state.usuario_nome = ""
                st.session_state.usuario_email = ""
            def rerun():
                st.rerun()

    

               
        else:
            st.markdown("**Não logado**")

    cpu = psutil.cpu_percent(interval=0.3)
    memoria = psutil.virtual_memory().percent
    df = atualizar_historico(cpu, memoria)

    left, right = st.columns([2,1])

    with left:
        c1, c2 = st.columns(2)
        with c1:
            cpu_color = "lime" if cpu < CPU_LIMITE else "red"
            st.markdown(f"<div style='background:#0f1720; padding:12px; border-radius:8px; text-align:center;'>"
                        f"<div style='font-size:44px; color:{cpu_color}; font-weight:700;'>{cpu:.1f}%</div>"
                        f"<div>CPU</div></div>", unsafe_allow_html=True)
        with c2:
            mem_color = "lime" if memoria < MEMORIA_LIMITE else "red"
            st.markdown(f"<div style='background:#0f1720; padding:12px; border-radius:8px; text-align:center;'>"
                        f"<div style='font-size:44px; color:{mem_color}; font-weight:700;'>{memoria:.1f}%</div>"
                        f"<div>Memória</div></div>", unsafe_allow_html=True)

        st.markdown("### Gráficos (últimos registros)")
        st.line_chart(df[["CPU (%)", "Memória (%)"]])

    with right:
        st.markdown("### Ações")
        retry = st.session_state.test_alert_retry
        target_email = st.session_state.usuario_email if st.session_state.usuario_logado and st.session_state.usuario_email else EMAIL_REMETENTE or "<defina EMAIL_REMETENTE no .env>"
        st.markdown(f"**E-mail alvo:** {target_email}")

        now = datetime.now()
        cooldown_until = retry.get("cooldown_until")
        seconds_left = max(0, int((cooldown_until - now).total_seconds())) if cooldown_until else 0

        if st.button("⚡ Enviar alerta de teste (uma tentativa)"):
            if not st.session_state.usuario_logado:
                st.warning("Você precisa estar logado para enviar alertas de teste.")
            else:
                cpu_test = cpu
                memoria_test = memoria
                alerta_msg = f"⚠️ ALERTA DE TESTE! CPU: {cpu_test:.1f}%, MEMÓRIA: {memoria_test:.1f}%"
                corpo_html = f"""
                <html><body>
                <h2 style='color:red;'>Alerta de Teste</h2>
                <p>CPU: <b>{cpu_test:.1f}%</b></p>
                <p>Memória: <b>{memoria_test:.1f}%</b></p>
                <p>Este e-mail foi enviado para: <b>{target_email}</b></p>
                </body></html>
                """
                ok_email = enviar_email(target_email, "Alerta de Teste - Monitor Inteligente", corpo_html)
                ok_telegram = enviar_telegram(alerta_msg)
                if ok_email or ok_telegram:
                    st.success(f"Alerta de teste enviado para {target_email} (e Telegram).")
                    st.session_state.alertas_historico.insert(0, f"TEST -> {alerta_msg} -> {target_email}")
                    st.session_state.test_alert_retry = {"attempts_left": 0, "cooldown_until": None, "last_target": ""}
                else:
                    st.error("Falha no envio agora. Você pode tentar novamente após o cooldown.")
                    st.session_state.test_alert_retry = {"attempts_left": 3, "cooldown_until": datetime.now() + timedelta(seconds=10), "last_target": target_email}

        st.markdown("---")
        retry = st.session_state.test_alert_retry
        if retry.get("attempts_left", 0) > 0:
            st.markdown(f"**Tentativas restantes:** {retry['attempts_left']}")
            if seconds_left > 0:
                st.info(f"Você pode tentar novamente em {seconds_left} s")
                st.button("Tentar agora (aguarde...)", disabled=True)
            else:
                if st.button("Tentar novamente agora"):
                    target = retry.get("last_target") or target_email
                    cpu_test = cpu
                    memoria_test = memoria
                    alerta_msg = f"⚠️ ALERTA DE TESTE! CPU: {cpu_test:.1f}%, MEMÓRIA: {memoria_test:.1f}%"
                    corpo_html = f"""
                    <html><body>
                    <h2 style='color:red;'>Alerta de Teste</h2>
                    <p>CPU: <b>{cpu_test:.1f}%</b></p>
                    <p>Memória: <b>{memoria_test:.1f}%</b></p>
                    <p>Este e-mail foi enviado para: <b>{target}</b></p>
                    </body></html>
                    """
                    ok_email = enviar_email(target, "Alerta de Teste - Monitor Inteligente", corpo_html)
                    ok_telegram = enviar_telegram(alerta_msg)
                    if ok_email or ok_telegram:
                        st.success(f"Alerta de teste enviado com sucesso para {target}.")
                        st.session_state.alertas_historico.insert(0, f"TEST -> {alerta_msg} -> {target}")
                        st.session_state.test_alert_retry = {"attempts_left": 0, "cooldown_until": None, "last_target": ""}
                    else:
                        attempts_left = max(0, retry.get("attempts_left", 1) - 1)
                        st.session_state.test_alert_retry["attempts_left"] = attempts_left
                        if attempts_left > 0:
                            st.session_state.test_alert_retry["cooldown_until"] = datetime.now() + timedelta(seconds=10)
                            st.error(f"Falha novamente. {attempts_left} tentativas restantes. Aguardar 10s antes de tentar.")
                        else:
                            st.error("Não foi possível enviar após todas as tentativas.")
                            st.session_state.test_alert_retry = {"attempts_left": 0, "cooldown_until": None, "last_target": ""}

        st.markdown("---")
        st.markdown("### Histórico de alertas (últimos 5)")
        for a in st.session_state.alertas_historico[:5]:
            st.write("-", a)

    if (cpu > CPU_LIMITE or memoria > MEMORIA_LIMITE):
        alerta_msg = f"⚠️ ALERTA! CPU: {cpu:.1f}%, MEMÓRIA: {memoria:.1f}%"
        tempo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        destinatario_real = st.session_state.usuario_email if st.session_state.usuario_logado else EMAIL_REMETENTE
        corpo_html = f"""
        <html><body>
        <h2 style='color:red;'>Alerta do Monitor Inteligente</h2>
        <p>CPU: <b>{cpu:.1f}%</b></p>
        <p>Memória: <b>{memoria:.1f}%</b></p>
        <p>Data/hora: {tempo}</p>
        </body></html>
        """
        enviar_email(destinatario_real, "Alerta - Monitor Inteligente", corpo_html)
        enviar_telegram(alerta_msg)
        st.session_state.alertas_historico.insert(0, f"{tempo} -> {alerta_msg} -> {destinatario_real}")