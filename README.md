# 🧠 Monitor Inteligente de Sistema

**Autor:** Emerson Brandão  
**Projeto:** Monitor de CPU e Memória com alertas automáticos  

---

## 🚀 Descrição
O **Monitor Inteligente** exibe métricas de CPU e memória em tempo real, enviando alertas automáticos por **E-mail** e **Telegram** quando os limites configurados são ultrapassados.  
Inclui **login, registro de usuário, recuperação de senha e histórico de alertas**.

---

## ⚙️ Funcionalidades Principais
- 📊 Dashboard em tempo real
- ⚠️ Alertas automáticos para CPU e memória
- ✉️ Envio de alertas por **E-mail**
- 🤖 Envio de alertas por **Telegram** (opcional)
- 🔑 Registro e login de usuários
- 🔄 Recuperação de senha temporária
- 📝 Histórico de alertas
- ⚡ Teste manual de alertas

---

## 📝 Requisitos
- Python 3.11+
- Pacotes listados em `requirements.txt`
- Conta Gmail para envio de e-mails
- Bot do Telegram (token e chat ID) opcional

---

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/emersonbrandao058-dot/monitor-inteligente.git
cd monitor-inteligente
Crie e ative o ambiente virtual:

bash
Copiar código
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux / MacOS
source venv/bin/activate
Instale as dependências:

bash
Copiar código
pip install -r requirements.txt
Configure as variáveis de ambiente:

Copie .env.exemplo para .env

Preencha com suas credenciais (DB, EMAIL, TELEGRAM)

▶️ Como rodar
bash
Copiar código
streamlit run main.py
Acesse: http://localhost:8502

📧 Alertas
Alertas automáticos quando CPU ou memória ultrapassam limites

Destinatário padrão: usuário logado ou e-mail do sistema

Teste de alerta manual disponível no dashboard

📂 Estrutura do Projeto
bash
Copiar código
monitor-inteligente/
│
├─ main.py           # Código principal
├─ alertas.py        # Envio de alertas
├─ db.py             # Funções de banco de dados
├─ utils.py          # Funções auxiliares
├─ requirements.txt  # Dependências
├─ .env.exemplo      # Modelo de variáveis de ambiente
├─ .gitignore
└─ README.md

⚠️ Observações
Nunca comite seu .env real (contém senhas)

Use .env.exemplo como referência