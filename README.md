# Discord Bot Panel

[English](#english) | [Čeština](#čeština)

---

# English

A comprehensive web panel for managing Python Discord bots. This application provides a user-friendly interface for bot management, with features for monitoring, controlling, and maintaining your Discord bot.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [First-time Setup](#first-time-setup)
- [Usage Guide](#usage-guide)
  - [Dashboard](#dashboard)
  - [Git Management](#git-management)
  - [Environment Variables](#environment-variables)
  - [File Editor](#file-editor)
  - [Requirements Management](#requirements-management)
  - [Webhook Configuration](#webhook-configuration)
  - [User Management](#user-management)
  - [Discord Settings](#discord-settings)
  - [IP Ban Management](#ip-ban-management)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **User Authentication System**
  - First user registered via web interface becomes admin
  - Additional users created through admin panel
  - Role-based access control (admin/user)
  - IP-based ban system after failed login attempts
  - User profile management with Discord ID integration

- **Bot Management**
  - Start, stop, and restart your bot
  - Real-time status monitoring (running state, PID, uptime)
  - Live console output with color highlighting
  - Separate virtual environment for the bot

- **Git Integration**
  - SSH key generation and management
  - Repository cloning
  - Manual git pull functionality
  - Automatic updates via webhooks

- **Environment Management**
  - Environment variable editor
  - Requirements installation
  - File editor for whitelisted files (e.g., `.env`)

- **Webhook System**
  - GitHub webhook integration
  - Automatic bot restart on commits with specific flags
  - Automatic requirements installation

- **Discord Integration**
  - Discord avatar fetching for users
  - Discord webhook status updates

- **UI Features**
  - Dark mode UI with Tailwind CSS
  - Responsive design
  - Real-time updates via WebSockets

## Requirements

- Python 3.10+
- Git
- Linux environment
- Internet connection (for Discord avatar fetching)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/stepanvalic/discord-bot-panel.git
   cd discord-bot-panel
   ```

2. Set up the virtual environment and install dependencies:
   ```bash
   make setup
   ```

3. Initialize the database:
   ```bash
   make db-init
   ```

4. Run the application:
   ```bash
   make run
   ```
   Alternatively, use the run.py script:
   ```bash
   python run.py
   ```

5. Access the panel at http://localhost:8000

## First-time Setup

1. Register the first admin user via the web interface
2. Set up your bot's repository:
   - Navigate to the GIT section
   - Generate SSH keys
   - Add the public key to your Git provider (GitHub, GitLab, etc.)
   - Clone your bot repository into the `work-bot` directory
3. Configure environment variables for your bot
4. Install bot requirements
5. Configure webhooks (if needed)

## Usage Guide

### Dashboard

The dashboard provides a central interface for monitoring and controlling your bot:

- **Status Panel**: Shows the current state of your bot (running/stopped), PID, uptime, and entrypoint file
- **Control Buttons**: Start, stop, and restart your bot
- **Console Output**: Real-time console logs with color highlighting for different message types

### Git Management

The Git section allows you to manage your bot's repository:

- **SSH Key Management**: Generate and view SSH keys for Git access
- **Repository Management**: Clone repositories and perform git pull operations
- **Requirements Installation**: Install Python dependencies from requirements.txt

### Environment Variables

The Environment Variables section allows you to configure your bot's environment:

- **Edit .env File**: Create or modify the .env file for your bot
- **Variable Management**: Add, edit, or remove environment variables

### File Editor

The File Editor provides a way to edit whitelisted files:

- **File Selection**: Choose from a list of editable files
- **Code Editor**: Edit file contents with syntax highlighting
- **Save Changes**: Save modifications directly from the panel

### Requirements Management

The Requirements section helps you manage your bot's Python dependencies:

- **View Requirements**: See the current requirements.txt file
- **Install Requirements**: Install dependencies with progress tracking
- **Installation Logs**: View logs from the installation process

### Webhook Configuration

The Webhook section allows you to set up automatic updates:

- **Webhook URL**: Generate a unique webhook URL for your repository
- **Webhook Key**: Configure a secure webhook key (32 characters with a mix of uppercase, lowercase, and numbers)
- **Message ID**: Set a Discord message ID for status updates (webhook will edit existing message instead of sending new ones)
- **Automatic Actions**: Configure automatic bot restart or requirements installation based on commit messages

#### Special Webhook Features

The webhook system includes special automation features triggered by specific commit message flags:

- **Automatic Bot Restart**: When a commit message contains `--restart`, the bot will automatically restart after the repository is updated
- **Automatic Requirements Installation**: When a commit message contains `--piprequest`, the system will automatically install pip requirements and then restart the bot
- **Local Device Compatibility**: Webhooks work locally on the device and are compatible with GitHub
- **Status Updates**: Webhook status for both panel and bot is sent using Discord embeds

### User Management

The User Management section (admin only) allows you to manage panel users:

- **Create Users**: Add new users with specified roles
- **Edit Users**: Modify user information and roles
- **Delete Users**: Remove users from the system

### Discord Settings

The Discord Settings section (admin only) allows you to configure Discord integration:

- **Avatar Updates**: Configure automatic avatar fetching for users
- **Webhook Settings**: Set up Discord webhooks for status updates

### IP Ban Management

The IP Ban Management section (admin only) allows you to manage banned IP addresses:

- **View Bans**: See a list of banned IP addresses
- **Unban IPs**: Remove IP addresses from the ban list

## Development

- Run the application with hot-reload:
  ```bash
  make run
  ```

- Clean Python cache files:
  ```bash
  make clean
  ```

## Troubleshooting

- **Bot Won't Start**: Check that the entrypoint file exists and is executable
- **Git Clone Fails**: Verify that your SSH key has been added to your Git provider
- **Webhook Not Working**: Ensure the webhook URL and key are correctly configured in your Git provider
- **Avatar Updates Not Working**: Check that your Discord bot token is correctly set up

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

# Čeština

Komplexní webový panel pro správu Python Discord botů. Tato aplikace poskytuje uživatelsky přívětivé rozhraní pro správu botů s funkcemi pro monitorování, ovládání a údržbu vašeho Discord bota.

## Obsah

- [Funkce](#funkce)
- [Požadavky](#požadavky)
- [Instalace](#instalace)
- [První nastavení](#první-nastavení)
- [Návod k použití](#návod-k-použití)
  - [Dashboard](#dashboard-1)
  - [Správa Gitu](#správa-gitu)
  - [Proměnné prostředí](#proměnné-prostředí)
  - [Editor souborů](#editor-souborů)
  - [Správa závislostí](#správa-závislostí)
  - [Konfigurace webhooků](#konfigurace-webhooků)
  - [Správa uživatelů](#správa-uživatelů)
  - [Nastavení Discordu](#nastavení-discordu)
  - [Správa IP banů](#správa-ip-banů)
- [Vývoj](#vývoj)
- [Řešení problémů](#řešení-problémů)
- [Licence](#licence)

## Funkce

- **Systém autentizace uživatelů**
  - První uživatel registrovaný přes webové rozhraní se stává administrátorem
  - Další uživatelé jsou vytvářeni přes administrátorský panel
  - Řízení přístupu na základě rolí (admin/uživatel)
  - Systém banování IP adres po neúspěšných pokusech o přihlášení
  - Správa uživatelských profilů s integrací Discord ID

- **Správa bota**
  - Spuštění, zastavení a restart bota
  - Monitorování stavu v reálném čase (stav běhu, PID, doba provozu)
  - Živý výstup konzole s barevným zvýrazněním
  - Samostatné virtuální prostředí pro bota

- **Integrace s Gitem**
  - Generování a správa SSH klíčů
  - Klonování repozitářů
  - Funkce manuálního git pull
  - Automatické aktualizace přes webhooky

- **Správa prostředí**
  - Editor proměnných prostředí
  - Instalace závislostí
  - Editor souborů pro povolené soubory (např. `.env`)

- **Systém webhooků**
  - Integrace s GitHub webhooky
  - Automatický restart bota při commitech se specifickými příznaky
  - Automatická instalace závislostí

- **Integrace s Discordem**
  - Načítání Discord avatarů pro uživatele
  - Aktualizace stavu přes Discord webhooky

- **Funkce UI**
  - Tmavý režim UI s Tailwind CSS
  - Responzivní design
  - Aktualizace v reálném čase přes WebSockety

## Požadavky

- Python 3.10+
- Git
- Linuxové prostředí
- Připojení k internetu (pro načítání Discord avatarů)

## Instalace

1. Naklonujte tento repozitář:
   ```bash
   git clone https://github.com/stepanvalic/discord-bot-panel.git
   cd discord-bot-panel
   ```

2. Nastavte virtuální prostředí a nainstalujte závislosti:
   ```bash
   make setup
   ```

3. Inicializujte databázi:
   ```bash
   make db-init
   ```

4. Spusťte aplikaci:
   ```bash
   make run
   ```
   Alternativně použijte skript run.py:
   ```bash
   python run.py
   ```

5. Přistupte k panelu na adrese http://localhost:8000

## První nastavení

1. Zaregistrujte prvního administrátora přes webové rozhraní
2. Nastavte repozitář vašeho bota:
   - Přejděte do sekce GIT
   - Vygenerujte SSH klíče
   - Přidejte veřejný klíč do vašeho Git poskytovatele (GitHub, GitLab, atd.)
   - Naklonujte repozitář bota do adresáře `work-bot`
3. Nakonfigurujte proměnné prostředí pro vašeho bota
4. Nainstalujte závislosti bota
5. Nakonfigurujte webhooky (pokud je potřeba)

## Návod k použití

### Dashboard

Dashboard poskytuje centrální rozhraní pro monitorování a ovládání vašeho bota:

- **Panel stavu**: Zobrazuje aktuální stav vašeho bota (běžící/zastavený), PID, dobu provozu a vstupní soubor
- **Ovládací tlačítka**: Spuštění, zastavení a restart bota
- **Výstup konzole**: Výstup konzole v reálném čase s barevným zvýrazněním pro různé typy zpráv

### Správa Gitu

Sekce Git umožňuje spravovat repozitář vašeho bota:

- **Správa SSH klíčů**: Generování a zobrazení SSH klíčů pro přístup ke Gitu
- **Správa repozitáře**: Klonování repozitářů a provádění operací git pull
- **Instalace závislostí**: Instalace Python závislostí z requirements.txt

### Proměnné prostředí

Sekce Proměnné prostředí umožňuje konfigurovat prostředí vašeho bota:

- **Úprava souboru .env**: Vytvoření nebo úprava souboru .env pro vašeho bota
- **Správa proměnných**: Přidání, úprava nebo odstranění proměnných prostředí

### Editor souborů

Editor souborů poskytuje způsob, jak upravovat povolené soubory:

- **Výběr souborů**: Výběr z seznamu upravitelných souborů
- **Editor kódu**: Úprava obsahu souborů se zvýrazněním syntaxe
- **Uložení změn**: Uložení úprav přímo z panelu

### Správa závislostí

Sekce Závislosti pomáhá spravovat Python závislosti vašeho bota:

- **Zobrazení závislostí**: Zobrazení aktuálního souboru requirements.txt
- **Instalace závislostí**: Instalace závislostí se sledováním průběhu
- **Instalační logy**: Zobrazení logů z procesu instalace

### Konfigurace webhooků

Sekce Webhook umožňuje nastavit automatické aktualizace:

- **URL webhooků**: Vygenerování jedinečné URL webhooků pro váš repozitář
- **Klíč webhooků**: Konfigurace bezpečného klíče webhooků (32 znaků s kombinací velkých, malých písmen a čísel)
- **ID zprávy**: Nastavení ID Discord zprávy pro aktualizace stavu (webhook upravuje existující zprávu místo posílání nových)
- **Automatické akce**: Konfigurace automatického restartu bota nebo instalace závislostí na základě zpráv commitů

#### Speciální funkce webhooků

Systém webhooků obsahuje speciální automatizační funkce spuštěné specifickými příznaky v commit zprávách:

- **Automatický restart bota**: Když commit zpráva obsahuje `--restart`, bot se automaticky restartuje po aktualizaci repozitáře
- **Automatická instalace závislostí**: Když commit zpráva obsahuje `--piprequest`, systém automaticky nainstaluje pip závislosti a poté restartuje bota
- **Kompatibilita s lokálním zařízením**: Webhooky fungují lokálně na zařízení a jsou kompatibilní s GitHubem
- **Aktualizace stavu**: Stav webhooků pro panel i bota je odesílán pomocí Discord embedů

### Správa uživatelů

Sekce Správa uživatelů (pouze pro adminy) umožňuje spravovat uživatele panelu:

- **Vytvoření uživatelů**: Přidání nových uživatelů s určenými rolemi
- **Úprava uživatelů**: Úprava informací o uživatelích a rolí
- **Odstranění uživatelů**: Odstranění uživatelů ze systému

### Nastavení Discordu

Sekce Nastavení Discordu (pouze pro adminy) umožňuje konfigurovat integraci s Discordem:

- **Aktualizace avatarů**: Konfigurace automatického načítání avatarů pro uživatele
- **Nastavení webhooků**: Nastavení Discord webhooků pro aktualizace stavu

### Správa IP banů

Sekce Správa IP banů (pouze pro adminy) umožňuje spravovat zakázané IP adresy:

- **Zobrazení banů**: Zobrazení seznamu zakázaných IP adres
- **Odblokování IP**: Odstranění IP adres ze seznamu banů

## Vývoj

- Spuštění aplikace s automatickým reloadem:
  ```bash
  make run
  ```

- Vyčištění Python cache souborů:
  ```bash
  make clean
  ```

## Řešení problémů

- **Bot se nespustí**: Zkontrolujte, zda vstupní soubor existuje a je spustitelný
- **Git clone selže**: Ověřte, že váš SSH klíč byl přidán do vašeho Git poskytovatele
- **Webhook nefunguje**: Ujistěte se, že URL a klíč webhooků jsou správně nakonfigurovány ve vašem Git poskytovateli
- **Aktualizace avatarů nefungují**: Zkontrolujte, že váš Discord bot token je správně nastaven

## Licence

Tento projekt je licencován pod licencí MIT - podrobnosti naleznete v souboru LICENSE.
