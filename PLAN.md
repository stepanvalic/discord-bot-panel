## 1. Přehled projektu
Cílem je vytvořit jednoduchý webový panel (solo script) pro správu jednoho Python Discord bota. Panel poběží v samostatném virtuálním prostředí (venv) a nabídne:

- Uživatelský systém (první uživatel CLI, další přes web)
- Zobrazení stavu bota a barevný výstup konzole (pro lepší orientaci v tmavém režimu)
- Ovládací prvky: Start, Restart, Stop
- Live konzolové logy s barevným zvýrazněním
- Správa SSH klíčů (generování, uložení, regenerace)
- Endpoint pro webhooky (uložení, zobrazení, regenerovatelné klíče)
- Prohlížení a úprava whitelisted souborů bota (např. `.env`)
- Databáze přes Supabase (konfigurace v `.env`)

## 2. Požadavky

### 2.1 Funkční požadavky
- Webový panel s přihlášením
  - První uživatel vytvořen přes CLI (interaktivní zadání username + heslo)
  - Další uživatelé spravováni přes webové rozhraní
- Zobrazení stavu bota: online/offline, PID, uptime
- Ovládací tlačítka: Start, Restart, Stop
- Live výstup konzole bota ve webu s barevnými tagy
- Generování a uložení SSH klíčů (256-bit) pro Git přístup
  - Možnost regenerace klíčů z webu
- Webhook server
  - Automaticky generovaný klíč ~30 náhodných znaků
  - Klíč lze regenerovat z webu
  - Po vložení webhook URL se uloží, zobrazí a umožní změnu
- Prohlížení a editace whitelistovaných souborů bota (`.env`, `config.yaml` apod.)
- Git integrace přes SSH
  - Klonování a `git pull` v adresáři `./bot/`
  - Při konfliktu upozornění ve webu / error log
- Databáze uživatelů a nastavení přes Supabase
  - Připojení definováno v `.env` (SUPABASE_URL, SUPABASE_KEY)

### 2.2 Ne-funkční požadavky
- Jediný spustitelný soubor (solo script)
- Provoz na Linux serveru v samostatném `venv`
- Bezpečné ukládání hesel (hash + salt)
- Ošetření chyb a centralizované logování aplikace
- Frontend v tmavém režimu s Tailwind CSS

## 3. Technologie
- **Jazyk**: Python 3.10+
- **Web framework**: FastAPI + Jinja2
- **CSS framework**: Tailwind CSS (dark mode)
- **ORM / DB**: Supabase (PostgreSQL)
- **Autentizace**: JWT + OAuth2 password flow
- **Log streaming**: WebSockets s barevným výstupem
- **SSH klíče**: Paramiko / `ssh-keygen`
- **Git klient**: `git` CLI via `subprocess`
- **Server**: Uvicorn

## 4. Architektura

```
+-------------------+      +----------------------+      +------------------------+
|  Uživatelský      | <--> |  Backend API         | <--> |  Supabase (PostgreSQL) |
|  prohlížeč        |      |  (FastAPI + Webhook) |      +------------------------+
+-------------------+      |                      |
                           |                      v
                           |                Git repo + bot venv
                           +----------------------+
```

## 5. Frontend
- Postranní menu pro navigaci (Dashboard, SSH klíče, Webhook, File Editor, Uživatelé, Env)
- Dark mode UI s Tailwind CSS
- Dashboard: stav bota, uptime, PID
- Konzolová sekce: live barevný výstup logu
- Formuláře pro SSH klíče a Webhook (zobrazení + regenerace)
- File Editor: výběr whitelistovaných souborů, editace a ukládání
- Správa uživatelů: seznam, role, vytváření
- Sekce Env: úprava `.env` proměnných (včetně Supabase)

## 6. Backend API

### 6.1 Autentizace
- CLI endpoint pro první uživatele: interaktivní prompt
- Webové endpointy CRUD pro uživatele a role
- OAuth2 / JWT autentizace pro všechny API routy

### 6.2 Bot management
- `GET /api/bot/status` – stav (running, pid, uptime)
- `POST /api/bot/start` – spawn subprocess `venv/bin/python bot.py`
- `POST /api/bot/stop` – ukončení procesu
- `POST /api/bot/restart` – restart subprocess

### 6.3 Logy
- WebSocket endpoint `/ws/logs` pro stream console v barevných tagách
- `GET /api/bot/logs?limit=n` – posledních n řádků z rotujících souborů

### 6.4 SSH klíče
- `GET /api/ssh-keys` – zobrazí veřejný klíč a info
- `POST /api/ssh-keys/generate` – regeneruje a uloží nový pár klíčů

### 6.5 Webhook
- `GET /api/webhook` – zobrazí aktuální URL a klíč
- `POST /api/webhook` – uloží nebo vymění URL
- `POST /api/webhook/regenerate` – vygeneruje nový ~30 znakový klíč
- `POST /webhook/receive` – přijímá Git payload, validuje HMAC, provede `git pull` a případný restart

### 6.6 File Editor
- `GET /api/files` – seznam whitelistovaných souborů
- `GET /api/files/{path}` – načte obsah
- `PUT /api/files/{path}` – uloží upravený obsah

### 6.7 Supabase env panel
- `GET /api/env` – vrátí proměnné
- `PUT /api/env` – aktualizuje `.env`

## 7. Databázový model
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ssh_public_key TEXT,
    ssh_private_key TEXT,
    webhook_url TEXT,
    webhook_key TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 8. Workflow a deployment

### 8.1 Lokální spuštění
1. `python3 -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### 8.2 (Později) Integrace do systemd
- Můžeme přidat službu až po stabilizaci feature setu

## 9. Bezpečnostní opatření
- HTTPS (Let's Encrypt)
- Bcrypt/Argon2 pro hesla
- Validace vstupů a CSRF ochrana (pokud se použije formulář)
- Ověření HMAC u webhook payloadů
- Omezený přístup k file editoru (whitelist)

## 10. Další kroky
1. Vytvoření skeletonu FastAPI projektu
2. Implementace databáze (Supabase)
3. CLI skript pro první uživatele
4. Autentizace a správa uživatelů
5. Bot management & log streaming
6. SSH klíče & Webhook
7. File Editor & Env panel
8. Frontend s Tailwind CSS (dark mode)
9. Testování a ladění
10. Dokumentace a nasazení

