#!/bin/bash

# Skript pro instalaci systémových závislostí potřebných pro Discord bota

echo "Instalace systémových závislostí pro Discord bota..."

# Aktualizace seznamu balíčků
apt-get update

# Instalace základních vývojových nástrojů
apt-get install -y build-essential python3-dev

# Instalace závislostí pro PyNaCl (pro hlasové funkce)
apt-get install -y libffi-dev

# Instalace závislostí pro opus (pro hlasové funkce)
apt-get install -y libopus-dev

# Instalace závislostí pro FFmpeg (pro hlasové funkce)
apt-get install -y ffmpeg

# Instalace dalších užitečných nástrojů
apt-get install -y git

echo "Instalace systémových závislostí dokončena."
echo "Nyní můžete nainstalovat Python závislosti pomocí:"
echo "pip install -r work-bot/requirements.txt"
