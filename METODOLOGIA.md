# Metodología — Andes Observatorio

**Versión:** 1.0  
**Fecha:** Septiembre 2026  
**Contacto:** andesobservatorio@gmail.com

---

## 1. Fuentes de Datos

### 1.1 Datos Geodésicos (SIRGAS)
- **Marco de referencia:** SIRGAS-CON (SIR22P01)
- **Tipo de datos:** Velocidades tectónicas (VN, VE, VU) y Retardo Troposférico Cenital (ZTD)
- **Formato:** SINEX TRO
- **Frecuencia de actualización:** Semanal
- **Latencia:** ~30 días (tiempo de publicación de SIRGAS)
- **Citación:** Mackern et al. (2020) - Productos troposféricos SIRGAS

### 1.2 Datos Meteorológicos
- **Fuente:** OpenWeatherMap
- **Cobertura:** 18 ciudades andinas
- **Frecuencia de actualización:** Cada 10 minutos
- **Variables:** Temperatura (°C), Humedad (%), Viento (m/s)

### 1.3 Calidad del Aire
- **Fuente:** OpenAQ API v3
- **Parámetro:** PM2.5 (µg/m³)
- **Frecuencia:** En tiempo real
- **Cobertura:** Bogotá, Medellín, Lima, Santiago

### 1.4 Escenarios Climáticos
- **Marco:** CMIP6 (SSP1-2.6, SSP2-4.5, SSP5-8.5)
- **Fuente:** IPCC AR6 (2021-2023)
- **Nota:** El simulador actual usa curvas ilustrativas. Se recomienda migrar a NEX-GDDP-CMIP6.

---

## 2. Anomalía ZTD

### Definición

### Período de referencia
- Actualmente: serie disponible de la API SIRGAS-TRO
- Recomendado: climatología 2014-2024 (10 años)

### Tratamiento de estacionalidad
- Se recomienda media móvil de 30 días para filtrar variabilidad diurna

### Clasificación visual
| Anomalía (mm) | Condición | Color |
|---------------|-----------|-------|
| > +15 | Muy húmedo | Azul intenso |
| +5 a +15 | Húmedo | Azul claro |
| -5 a +5 | Normal | Verde |
| -15 a -5 | Seco | Naranja |
| < -15 | Muy seco | Rojo |

---

## 3. Velocidades Tectónicas

### Clasificación geodésica
| Magnitud (mm/año) | Interpretación | Color |
|-------------------|----------------|-------|
| 0–5 | Intraplaca estable | Verde |
| 5–15 | Deformación media | Amarillo |
| 15–25 | Actividad tectónica | Naranja |
| >25 | Borde de placa | Rojo |

### Escala visual
- **Factor:** 1 mm/año ≈ 0.5 km en mapa
- **Nota:** NO es escala física, solo visualización

---

## 4. Alertas

### Alerta de precipitación

### Validación pendiente
- Comparación con pluviómetros IDEAM/SENAMHI
- Métricas: POD, FAR, CSI
- Fuente lluvia alternativa: CHIRPS

---

## 5. Limitaciones

1. Los datos no reemplazan a las agencias oficiales
2. El simulador actual es ilustrativo, no para decisiones
3. La anomalía ZTD requiere validación retrospectiva
4. AQI depende de disponibilidad de estaciones OpenAQ

---

## 6. Referencias Bibliográficas (APA 7ª edición)

### Datos Geodésicos

Mackern, M. V., Mateo, M. L., Camisay, M. F., & Rosell, P. A. (2020). *Tropospheric products from SIRGAS-CON: Methodology and applications*. Journal of Geodesy, 94(8), 1-15. https://doi.org/10.1007/s00190-020-01411-4

SIRGAS. (2026). *Sistema de Referencia Geocéntrico para las Américas*. https://sirgas.ipgh.org/

### Datos Meteorológicos

OpenWeatherMap. (2026). *Current weather and forecast API documentation*. https://openweathermap.org/api

IDEAM. (2026). *Instituto de Hidrología, Meteorología y Estudios Ambientales de Colombia*. http://www.ideam.gov.co/

SENAMHI. (2026). *Servicio Nacional de Meteorología e Hidrología del Perú*. https://www.senamhi.gob.pe/

### Calidad del Aire

OpenAQ. (2026). *Open air quality data platform*. https://openaq.org/

### Escenarios Climáticos

IPCC. (2023). *Climate change 2023: Synthesis report. Contribution of Working Groups I, II and III to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change*. (H. Lee & J. Romero, Eds.). IPCC. https://doi.org/10.59327/IPCC/AR6-9789291691647

O'Neill, B. C., Tebaldi, C., van Vuuren, D. P., Eyring, V., Friedlingstein, P., Hurtt, G., Knutti, R., Kriegler, E., Lamarque, J.-F., Lowe, J., Meehl, G. A., Moss, R., Riahi, K., & Sanderson, B. M. (2016). The Scenario Model Intercomparison Project (ScenarioMIP) for CMIP6. *Geoscientific Model Development*, 9(9), 3461-3482. https://doi.org/10.5194/gmd-9-3461-2016

### Deforestación

Global Forest Watch. (2026). *Deforestación y pérdida de cobertura arbórea en América Latina*. World Resources Institute. https://www.globalforestwatch.org/

### Acuerdo de Escazú

CEPAL. (2018). *Acuerdo Regional sobre el Acceso a la Información, la Participación Pública y el Acceso a la Justicia en Asuntos Ambientales en América Latina y el Caribe* (Acuerdo de Escazú). Naciones Unidas. https://www.cepal.org/es/acuerdodeescazu

### Herramientas

Leaflet. (2026). *Leaflet: An open-source JavaScript library for interactive maps*. https://leafletjs.com/

Chart.js. (2026). *Chart.js: Simple yet flexible JavaScript charting*. https://www.chartjs.org/

FastAPI. (2026). *FastAPI: Modern web framework for building APIs with Python*. https://fastapi.tiangolo.com/

---

## 7. Citación

Si usa estos datos, cite:

Sierra Bernal, M. J. (2026). *Andes Observatorio: Plataforma de monitoreo geodésico y ambiental para la región andina* [Aplicación web]. https://andesobservatorio.github.io/andes-observatorio/



---

## 8. Módulos de Análisis Científico

### 8.1 Mecanismo C: Correlación ZTD vs Precipitación

**Objetivo:** Verificar si la anomalía de ZTD predice eventos de precipitación en la región andina.

**Datos:**
- **ZTD:** SIRGAS-CON (soluciones horarias, latencia ~30 días)
- **Precipitación:** Open-Meteo Historical API (datos diarios desde 1940)

**Metodología:**
1. Promedio diario del ZTD horario
2. Anomalía ZTD = ZTD_diario − media móvil 30 días
3. Correlación de Spearman (no paramétrica)
4. Nivel de significancia: α = 0.05

**Resultados:**
Ver `analysis/REPORTE_MECANISMO_C.md` para el análisis detallado de la estación BOGT.

**Interpretación:**
La correlación positiva entre anomalía ZTD y precipitación diaria confirma que el vapor de agua atmosférico medido por GNSS es un indicador útil para el monitoreo de precipitación. Sin embargo, el ZTD no muestra capacidad predictiva con 1 día de antelación (p = 0.98), lo que indica que ambos fenómenos son sincrónicos en la escala diaria.

### 8.2 Mecanismo A: Desplazamiento Vertical GNSS vs Pérdida Glaciar (En desarrollo)

**Objetivo:** Verificar si la pérdida de masa glaciar genera levantamiento elástico cortical medible con GNSS.

**Datos:**
- **GNSS vertical:** SIRGAS-CON (componente U)
- **Balance de masa glaciar:** WGMS, IDEAM, estudios académicos

**Estado:** Pendiente de implementación

### 8.3 Mecanismo B: Carga Hidrológica vs Microsismicidad (En desarrollo)

**Objetivo:** Explorar si los cambios de carga hidrológica modulan la microsismicidad regional.

**Datos:**
- **GNSS vertical:** SIRGAS-CON
- **Sismicidad:** SGC Colombia, IGP Perú
- **Carga hidrológica:** GRACE, CHIRPS

**Estado:** Pendiente de implementación

---

## 9. Declaración de Integridad Científica

Los datos SIRGAS en esta plataforma se utilizan para verificar exploratoriamente hipótesis de acoplamiento clima-Tierra sólida (Mecanismos A, B y C). Todos los análisis de correlación muestran resultados de pruebas estadísticas (valor p, intervalos de confianza). La separación de componentes no tectónicas en señales de desplazamiento vertical tiene incertidumbre. Los datos de esta plataforma no sustituyen las publicaciones oficiales de cada institución, ni se utilizan para decisiones de alerta temprana.
