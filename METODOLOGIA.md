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

## 6. Citación

Si usa estos datos, cite:

> Sierra Bernal, M.J. (2026). Andes Observatorio: Plataforma de monitoreo geodésico y ambiental para la región andina. https://andesobservatorio.github.io/andes-observatorio/
