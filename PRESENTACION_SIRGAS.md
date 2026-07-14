# 🌄 Andes Observatorio: Plataforma de Monitoreo Ambiental y Geodésico

## Simposio SIRGAS 2026 - Montevideo, Uruguay

### 🎯 Objetivo
Presentar una plataforma de código abierto que integra datos climáticos y geodésicos (SIRGAS) para el monitoreo ambiental en la región andina.

### 📊 Datos Integrados
- **OpenWeatherMap**: Temperatura, humedad, presión (tiempo real)
- **SIRGAS-CON**: Velocidades tectónicas y ZTD (Retardo Troposférico Cenital)
- **Áreas protegidas**: Porcentaje de territorio protegido por país
- **Normativas ambientales**: Marco legal por país

### 🛠️ Tecnologías
- **Frontend**: HTML5, CSS3, JavaScript, Leaflet, Chart.js
- **Backend**: FastAPI, Python, SQLAlchemy
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Despliegue**: GitHub Actions, Render

### 📈 Resultados
- 5+ estaciones SIRGAS monitoreadas en la región andina
- 20,440+ observaciones de ZTD procesadas
- Dashboard interactivo con visualizaciones en tiempo real
- Histórico de datos desde diciembre 2025

### 🔗 Enlaces
- [Dashboard en vivo](https://andesobservatorio.github.io/andes-observatorio/)
- [Repositorio en GitHub](https://github.com/AndesObservatorio/andes-observatorio)
- [Documentación técnica](https://github.com/AndesObservatorio/andes-observatorio/blob/main/README.md)

### 📧 Contacto
**María J. Sierra Bernal**
Investigador Principal / Fundadora
andesobservatorio@gmail.com
+57 3337211047

### Cita Obligatoria
Mackern M.V., Mateo M.L., Camisay M.F., Morichetti P.V. (2020). *Tropospheric Products from High-Level GNSS Processing in Latin America*. IAG Symposia Series, Vol 152. doi: 10.1007/1345_2020_121

---

## 📋 Resumen Técnico para el Simposio

### Metodología
1. **Ingesta de datos**: Pipeline automatizado que descarga archivos SINEX TRO del FTP de SIRGAS
2. **Procesamiento**: Parseo de archivos y almacenamiento en base de datos SQLite
3. **Visualización**: Dashboard interactivo con gráficos y mapas
4. **API**: Endpoints REST para consultar datos en tiempo real

### Próximos pasos
- Escalar a cobertura global de estaciones SIRGAS
- Implementar alertas automáticas basadas en umbrales de ZTD
- Integrar datos de otras redes GNSS (IGS, RING)

### Agradecimientos
- SIRGAS por los datos abiertos
- AECID por el apoyo a la cooperación triangular
- Universidad Distrital Francisco José de Caldas
- Universidad Nacional de Loja - Proyecto WateRS
