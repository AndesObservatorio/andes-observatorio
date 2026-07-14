#!/bin/bash
cd ~/andes-observatorio

# Hacer backup del dashboard
cp dashboard.html dashboard.html.bak

# Actualizar el tile server en el dashboard
sed -i 's|https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png|https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png|g' dashboard.html

echo "✅ Tile server actualizado. Recarga el dashboard con Ctrl+Shift+R"
