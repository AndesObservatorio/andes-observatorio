#!/bin/bash
echo "🚀 Iniciando API SIRGAS..."

# Matar procesos anteriores
pkill -f sirgas_api.py 2>/dev/null
sudo fuser -k 8001/tcp 2>/dev/null

# Esperar 1 segundo
sleep 1

# Iniciar API
cd ~/andes-observatorio
source venv/bin/activate
echo "🛰️ Iniciando API en puerto 8001..."
python sirgas_api.py
