# Andes Observatorio: Plataforma de monitoreo geodésico y ambiental para la región andina

**Autora:** María J. Sierra Bernal  
**Estudiante de la Especialización en Gestión Ambiental**  
Investigadora Principal - Andes Observatorio  
Creadora y desarrolladora del proyecto

**Contacto:** andesobservatorio@gmail.com · jbersiel@gmail.com · +57 3337211047  
**Plataforma:** https://andesobservatorio.github.io/andes-observatorio/dashboard.html  
**GitHub:** https://github.com/AndesObservatorio/andes-observatorio

**Contexto:** Preparado para el Simposio SIRGAS 2026 · Montevideo, Uruguay · 3-6 noviembre 2026

---

## Resumen ejecutivo

Andes Observatorio es una plataforma de código abierto que integra datos geodésicos de la red SIRGAS-CON con variables ambientales para el monitoreo climático en la región andina. El proyecto demuestra la aplicabilidad práctica de los productos troposféricos SIRGAS — específicamente el Retardo Troposférico Cenital (ZTD) — como indicador del contenido de vapor de agua atmosférico y su correlación con eventos de precipitación.

La plataforma integra **13 estaciones GNSS SIRGAS**, de las cuales **5 cuentan con series temporales completas** que permiten el análisis de correlación ZTD-precipitación mediante el coeficiente de Spearman. Los resultados muestran **correlaciones positivas significativas (r > 0.3, p < 0.0001) en 4 de 5 estaciones analizadas**: Bogotá (r = 0.397), Cali (r = 0.507), Arequipa (r = 0.363) y Santiago (r = 0.326). La estación Antofagasta no muestra correlación significativa (r = −0.044), resultado consistente con su ubicación en una zona árida del desierto de Atacama.

El proyecto se materializa en **cuatro componentes interconectados**:

1. **Dashboard de monitoreo** — visualización interactiva de ZTD, velocidades tectónicas y variables climáticas en tiempo real.
2. **Análisis multi-estación ZTD-precipitación** — correlación de Spearman entre anomalías ZTD y precipitación diaria.
3. **Simulador de deformación volcánica** — modelo de fuentes Mogi, sill y dique para deformación superficial.
4. **Sistema de respaldo offline** — garantiza la disponibilidad de los datos sin conexión a internet.

La plataforma está desarrollada con tecnologías de código abierto (HTML5, JavaScript, Python/FastAPI, Leaflet, Plotly) y desplegada en GitHub Pages y Render.com. El proyecto se alinea con los objetivos del **Simposio SIRGAS 2026** y la **Agenda 2030** (ODS 13 y 15).

**Palabras clave:** SIRGAS · ZTD · GNSS · vapor de agua · monitoreo ambiental · región andina.

---

## 1. Contexto y motivación

La región andina concentra el 99% de los glaciares tropicales del mundo y es fuente de agua para más de 50 millones de personas. Desde 1960, la temperatura media ha aumentado +1.5°C, superando el promedio global, lo que acelera el retroceso glaciar y altera los patrones de precipitación. Los modelos climáticos proyectan una reducción del 30% al 50% en la disponibilidad hídrica andina para 2050 bajo escenarios RCP 8.5.

Frente a este contexto, la información climática y geodésica disponible se encuentra fragmentada en múltiples instituciones sin interoperabilidad, limitando su uso para la toma de decisiones. Andes Observatorio nace para abordar esta brecha, integrando datos SIRGAS en una plataforma accesible que democratiza el acceso a información geoespacial de calidad.

---

## 2. Componentes del proyecto

### 2.1 Dashboard de monitoreo en tiempo real

Panel interactivo que visualiza en tiempo real:
- Datos climáticos (temperatura, humedad) de OpenWeatherMap para 18 ciudades andinas
- Mapa de estaciones SIRGAS con vectores de velocidad tectónica
- Mapa ZTD con 13 estaciones y anomalías respecto al promedio histórico
- Calidad del aire (AQI, PM2.5) para 26 ciudades andinas vía OpenAQ
- Gráficos comparativos por país y series temporales

### 2.2 Análisis multi-estación ZTD ↔ precipitación

Módulo de análisis científico que calcula la correlación de Spearman entre la anomalía ZTD y la precipitación diaria en cinco estaciones SIRGAS con series completas. La anomalía ZTD se define como la diferencia entre el valor actual y el promedio histórico de cada estación, eliminando el sesgo altitudinal y permitiendo comparaciones atmosféricas entre estaciones de distintas elevaciones.

### 2.3 Simulador de deformación volcánica

Herramienta interactiva que modela fuentes de deformación superficial mediante los modelos clásicos Mogi (fuente puntual), sill (fuente tabular horizontal) y dique (fuente tabular vertical). El simulador permite ajustar parámetros de profundidad, volumen, posición y visualizar la superficie de deformación en 3D.

### 2.4 Sistema de respaldo offline

Arquitectura de resiliencia que garantiza la disponibilidad del dashboard sin conexión a internet. El sistema prioriza los datos en tiempo real desde Render.com y, ante cualquier fallo, carga automáticamente datos respaldados localmente, indicando visualmente el origen de la información (🔴 En vivo / 📁 Respaldo).

---

## 3. Estado actual de desarrollo

| Componente | Estado (octubre 2026) |
|---|---|
| Estaciones ZTD integradas | 13 (5 con series completas) |
| Análisis multi-estación | 5 estaciones analizadas |
| Correlaciones significativas | 4 de 5 (r > 0.3, p < 0.0001) |
| Ciudades climáticas | 18 |
| Ciudades AQI | 26 |
| Anomalías ZTD | ±75 mm |
| Simulador volcánico | Operativo (Mogi/Sill/Dique) |
| Respaldo offline | Operativo (448 KB) |
| Traducción | Español · English · Português |
| Licencia | MIT (código abierto) |

---

## 4. Alineación con SIRGAS 2026

El proyecto contribuye directamente a los objetivos del Simposio SIRGAS 2026 en tres ejes:

- **Uso práctico del marco SIRGAS:** demuestra la aplicabilidad de los productos troposféricos (ZTD) más allá de la geodesia pura, conectándolos con monitoreo ambiental y gestión del riesgo climático.
- **Colaboración regional:** plataforma escalable y replicable, diseñada para estandarizar metodologías e intercambiar información entre países andinos.
- **Agenda 2030:** apoya los ODS 13 (Acción por el clima) y 15 (Vida de ecosistemas terrestres).

---

## 5. Próximos pasos

**Corto plazo (3-6 meses):**
- Optimización de la latencia del pipeline (~30 días → ~7 días)
- Mapa de calor ZTD para distribución espacial del vapor de agua
- Ampliación del análisis multi-estación a 13 estaciones

**Mediano plazo (6-12 meses):**
- Integración con índices de calidad del aire (AQI) en más ciudades
- Módulo de monitoreo de deforestación con datos satelitales
- Aplicación móvil PWA para acceso ciudadano

**Largo plazo (1-2 años):**
- Modelos de pronóstico con inteligencia artificial
- API pública abierta para investigadores
- Alianzas institucionales con IDEAM, SENAMHI, INAIGEM y universidades andinas
- Integración con redes GNSS internacionales (IGS, ITRF)

---

## 6. Reconocimientos

Esta investigación ha sido posible gracias al apoyo de:

- **International Association of Geodesy (IAG):** beneficiaria de la beca *IAG International Travel Award* (€1,000) para asistencia al Simposio SIRGAS 2026.
- **SIRGAS / IPGH:** por la organización del Simposio y la disponibilidad abierta de los datos SIRGAS-CON y SIRGAS-TRO.
- **Corporación Universitaria Asturias:** por el aval institucional otorgado para la participación en el Simposio SIRGAS 2026.
- **Comunidad de código abierto:** por las herramientas utilizadas (Leaflet, Plotly, OpenStreetMap, Python/FastAPI).

---

**Contacto:** andesobservatorio@gmail.com · +57 3337211047  
**Plataforma:** https://andesobservatorio.github.io/andes-observatorio/  
**GitHub:** https://github.com/AndesObservatorio/andes-observatorio  
**Licencia:** MIT

---

*Última actualización: octubre 2026*
