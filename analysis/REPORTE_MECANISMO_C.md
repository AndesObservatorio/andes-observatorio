# Mecanismo C: Correlación ZTD vs Precipitación

**Fecha:** Septiembre 2026
**Estación:** BOGT (Bogotá, Colombia) - lat 4.64, lon -74.08
**Período:** 2025-12-15 a 2026-06-06 (174 días)

## Objetivo
Verificar si la anomalía de ZTD (Retardo Troposférico Cenital) predice eventos de precipitación en la región andina.

## Datos
- **ZTD:** SIRGAS-CON, estación BOGT (4,008 registros horarios)
- **Precipitación:** Open-Meteo Historical API (174 registros diarios)

## Metodología
1. Promedio diario del ZTD horario
2. Anomalía ZTD = ZTD_diario − media móvil 30 días
3. Correlación de Spearman (no paramétrica)
4. Nivel de significancia: α = 0.05

## Resultados

| Métrica | Valor |
|---------|-------|
| N observaciones | 138 |
| Correlación Spearman (r) | **0.397** |
| Valor p | **< 0.0001** |
| Significancia | ✅ SIGNIFICATIVA |

### Interpretación
Existe una correlación positiva moderada y estadísticamente significativa entre la anomalía ZTD y la precipitación diaria en Bogotá. Esto confirma que el vapor de agua atmosférico medido por GNSS es un indicador útil para el monitoreo de precipitación.

## Limitaciones
- Análisis limitado a una estación (BOGT)
- Período de 6 meses (no incluye ciclo anual completo)
- No se controló por estacionalidad

## Próximos pasos
1. Replicar el análisis en las 13 estaciones ZTD
2. Extender el período a 2+ años
3. Análisis de retardo temporal (lag)

## Citación
Sierra Bernal, M.J. (2026). Mecanismo C: Correlación ZTD vs Precipitación. Andes Observatorio.

---

## Análisis de Retardo Temporal

Se evaluó la correlación cruzada para lags de -5 a +5 días:

| Lag (días) | Spearman r | Valor p |
|------------|------------|---------|
| -5 | 0.034 | 0.6938 |
| -3 | -0.109 | 0.2033 |
| -1 | 0.091 | 0.2909 |
| **0** | **0.397** | **< 0.0001 ⭐** |
| +1 | 0.091 | 0.2909 |
| +3 | -0.109 | 0.2033 |
| +5 | 0.034 | 0.6938 |

**Interpretación:** La correlación máxima ocurre en **lag = 0** (mismo día). El ZTD y la precipitación son fenómenos sincrónicos en la escala diaria.

### Test de predicción (ZTD alto → precipitación día siguiente)

| ZTD alto | Precipitación día siguiente | Casos |
|----------|----------------------------|-------|
| No | No | 112 |
| No | Sí | 20 |
| Sí | No | 29 |
| Sí | Sí | 6 |

Chi-cuadrado: 0.001, p = 0.9787 → **Sin capacidad predictiva con 1 día de antelación**

**Implicación:** El ZTD no es un predictor de precipitación a corto plazo (1 día), pero sí es un **indicador simultáneo** del contenido de vapor de agua atmosférico.
