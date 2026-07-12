# Andes-Observa
mardown
# 🌄 Andes Observatorio

[![GitHub Pages](https://img.shields.io/badge/website-up-brightgreen)](https://andesobservatorio.github.io/andes-observatorio/)
[![OpenWeatherMap](https://img.shields.io/badge/API-OpenWeatherMap-blue)](https://openweathermap.org/)
[![Leaflet](https://img.shields.io/badge/maps-Leaflet-green)](https://leafletjs.com/)
[![Chart.js](https://img.shields.io/badge/charts-Chart.js-red)](https://www.chart.js/)

## 📊 Monitoreo ambiental de la región andina en tiempo real

**Andes Observatorio** es una plataforma interactiva que monitorea y visualiza datos ambientales de los países de la región andina en tiempo real. Combina datos meteorológicos, áreas protegidas y visualización geográfica para ofrecer una herramienta completa de monitoreo.

---

## ✨ Características principales

| Característica | Descripción |
|----------------|-------------|
| 🌡️ **Temperatura en vivo** | Datos reales de OpenWeatherMap para 7 capitales andinas |
| 🗺️ **Mapa interactivo** | Visualización geográfica con marcadores y popups |
| 📈 **Gráficos comparativos** | Temperaturas por país y áreas protegidas |
| 🔄 **Actualización automática** | Datos refrescados cada 10 minutos |
| 📍 **Selector de ciudades** | Cambia entre capitales andinas fácilmente |

---

## 🗺️ Países incluidos

| País | Capital | Temperatura promedio |
|------|---------|---------------------|
| 🇨🇴 Colombia | Bogotá | 14-18°C |
| 🇪🇨 Ecuador | Quito | 16-20°C |
| 🇵🇪 Perú | Lima | 18-22°C |
| 🇧🇴 Bolivia | La Paz | 12-16°C |
| 🇨🇱 Chile | Santiago | 12-18°C |
| 🇦🇷 Argentina | Buenos Aires | 16-22°C |
| 🇧🇷 Brasil | Brasilia | 20-26°C |

> Próximamente: 🇻🇪 Venezuela, 🇵🇦 Panamá

---

## 🛠️ Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| HTML5, CSS3, JavaScript | Frontend |
| [Chart.js](https://www.chart.js/) | Gráficos interactivos |
| [Leaflet](https://leafletjs.com/) | Mapas interactivos |
| [OpenWeatherMap API](https://openweathermap.org/) | Datos climáticos en tiempo real |
| GitHub Pages | Alojamiento gratuito |

---

## 📁 Estructura del proyecto
# Andes-Observa
andes-observatorio/
│
├── index.html # Landing page institucional
├── dashboard.html # Dashboard interactivo principal
├── README.md # Documentación del proyecto
│
└── assets/ # (futuro) Imágenes y recursos
text


---

## 🚀 Ver en vivo

### 🔗 [https://andesobservatorio.github.io/andes-observatorio/](https://andesobservatorio.github.io/andes-observatorio/)

### Acceso directo:
- **Landing page:** [index.html](https://andesobservatorio.github.io/andes-observatorio/)
- **Dashboard:** [dashboard.html](https://andesobservatorio.github.io/andes-observatorio/dashboard.html)

---

## 📸 Capturas de pantalla

*(Puedes agregar imágenes de tu dashboard aquí después)*

---

## 🛰️ Módulo geodésico SIRGAS

Además del dashboard ambiental, el proyecto expone una API geodésica basada en datos de la red **SIRGAS-CON**:

| Dato | Endpoint | Fuente |
|------|----------|--------|
| Velocidades de estaciones | `GET /api/v1/geodesia/velocidades` | `SIR22P01_velocities.txt` (SIRGAS) |
| Estación puntual | `GET /api/v1/geodesia/estacion/{id}` | ídem |
| Estaciones con datos troposféricos | `GET /api/v1/geodesia/tropo/estaciones` | Base de datos local |
| Serie histórica de ZTD por estación | `GET /api/v1/geodesia/tropo/{codigo}/serie?desde=&hasta=` | Base de datos local |

### Parámetros troposféricos (ZTD)

Se ingiere el **Retardo Troposférico Cenital (ZTD)** que SIRGAS publica en formato **SINEX TRO**, con muestreo horario, desde enero de 2014, vía `ftp://ftp.sirgas.org/pub/gps/SIRGAS-ZPD/` (redirige a `www3.dgfi.tum.de`). SIRGAS publica estos productos semanalmente con ~30 días de latencia, por lo que no es un dato "en vivo": se ingiere periódicamente a una base de datos (SQLite en desarrollo, Postgres en producción vía `DATABASE_URL`).

**Estructura real del FTP** (confirmada explorando manualmente el servidor):
```
/pub/gps/SIRGAS-ZPD/<año>/<día-del-año, 3 dígitos>/{ESTACION}{ddd}0.{yy}zpd.gz
```
Es decir: **un archivo comprimido (.gz) por estación por día** — toda la red SIRGAS-CON tiene ~400+ estaciones.

**Cobertura de estaciones (config/stations.py):**
Por defecto, el pipeline solo procesa las 12 estaciones que ya muestra el dashboard actual (`scope="andes"`: Colombia, Ecuador, Perú, Bolivia, Chile, Argentina). El código ya está preparado para escalar a cobertura mundial sin tocar el fetcher ni el parser — solo hay que:

```bash
# Uso normal (default): solo las estaciones del dashboard
python sirgas_tropo_ingest.py --days-back 60

# Escalar a TODAS las estaciones de SIRGAS-CON (~400+), sin cambiar código:
python sirgas_tropo_ingest.py --days-back 60 --scope global

# Agregar una nueva región (ej. Centroamérica) más adelante: solo se
# agrega una entrada en config/stations.py -> REGIONES, y se usa:
python sirgas_tropo_ingest.py --days-back 60 --scope centroamerica

# Override manual puntual, ignorando el scope:
python sirgas_tropo_ingest.py --days-back 60 --stations BOGT,QUIT,AACR,LPGS
```

Pipeline:
```
config/stations.py        -> qué estaciones procesar (por región/scope, o "global" = todas)
sirgas_tropo_fetcher.py   -> descarga los .zpd.gz diarios por FTP, reutilizando una
                              única conexión (reconecta automáticamente si se cae),
                              con caché local para no volver a bajar lo ya descargado
sirgas_tropo_parser.py    -> parsea el formato SINEX TRO real (lee el orden de columnas
                              del propio archivo vía TROP/DESCRIPTION, no lo asume fijo)
sirgas_tropo_ingest.py    -> orquesta descarga + parseo + guardado idempotente en DB
```

Para correr la ingesta manualmente:
```bash
pip install -r requirements.txt
python sirgas_tropo_ingest.py --days-back 60
```

**Citación obligatoria:** el uso de estos productos requiere citar a Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020). *Tropospheric Products from High-Level GNSS Processing in Latin America*. IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121

---

## 🎯 Próximas mejoras

- [ ] Agregar Venezuela y Panamá al dashboard
- [ ] Gráfico de tendencia histórica de temperatura
- [ ] Sección de noticias ambientales
- [ ] Calidad del aire (AQI) en tiempo real
- [ ] Datos de deforestación por país

---

## 📧 Contacto

| Medio | Información |
|-------|-------------|
| 📧 Correo | andesobservatorio@gmail.com |
| 📞 Teléfono | +57 3337211047 |
| 🌐 Web | [GitHub Pages](https://andesobservatorio.github.io/andes-observatorio/) |

---

## 📄 Licencia

Este proyecto es de código abierto y está disponible para fines educativos y de conservación ambiental.

---

*🌄 Andes Observatorio - Monitoreo de ecosistemas andinos para su protección y conservación*

*Datos actualizados en tiempo real desde OpenWeatherMap*

