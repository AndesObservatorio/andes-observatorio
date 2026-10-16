import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime

# ============================================================
# INICIALIZAR APP
# ============================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'],
                suppress_callback_exceptions=True)
server = app.server

# ============================================================
# DATOS DEMO EMBEBIDOS (Fallback cuando no existan JSON)
# ============================================================
NORMAS_DEMO = {
    'colombia': [
        {"id": "co-001", "titulo": "Ley 1523 de 2012", "estado": "activa", "tema": "SNGRD - Gestión del Riesgo", "ambito": "Nacional", "url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=47017", "territorios_afectados": ["Nukak", "Embera", "Wayúu"], "lat": 4.57, "lon": -74.30, "ano": 2012, "escazu_pilar": "Acceso a la información"},
        {"id": "co-002", "titulo": "Decreto 1076 de 2015", "estado": "activa", "tema": "Sector Ambiente", "ambito": "Nacional", "url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=78153", "territorios_afectados": ["Misak", "Arhuaco", "Nukak"], "lat": 4.60, "lon": -74.08, "ano": 2015, "escazu_pilar": "Participación ciudadana"},
        {"id": "co-003", "titulo": "Ley 1955 de 2019", "estado": "activa", "tema": "PND - Plan Nacional Desarrollo", "ambito": "Nacional", "url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=89516", "territorios_afectados": ["Wayúu", "Embera"], "lat": 4.65, "lon": -74.10, "ano": 2019, "escazu_pilar": "Justicia ambiental"},
        {"id": "co-004", "titulo": "Decreto 2099 de 2021", "estado": "revision", "tema": "Ordenamiento Territorial", "ambito": "Nacional", "url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=116", "territorios_afectados": ["Nukak", "Misak"], "lat": 2.50, "lon": -72.50, "ano": 2021, "escazu_pilar": "Participación ciudadana"},
        {"id": "co-005", "titulo": "Ley 2166 de 2021", "estado": "activa", "tema": "Acción Climática", "ambito": "Nacional", "url": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=117", "territorios_afectados": ["Wayúu", "Arhuaco", "Embera"], "lat": 11.00, "lon": -72.80, "ano": 2021, "escazu_pilar": "Acceso a la información"},
    ],
    'peru': [
        {"id": "pe-001", "titulo": "Ley 28611 - Ley General del Ambiente", "estado": "activa", "tema": "Marco ambiental", "ambito": "Nacional", "url": "https://www.minam.gob.pe/ley-general-del-ambiente/", "territorios_afectados": ["Asháninka", "Awajún"], "lat": -12.05, "lon": -77.04, "ano": 2005, "escazu_pilar": "Justicia ambiental"},
        {"id": "pe-002", "titulo": "Ley 29785 - Consulta Previa", "estado": "activa", "tema": "Derechos indígenas", "ambito": "Nacional", "url": "https://www.minem.gob.pe/", "territorios_afectados": ["Asháninka", "Awajún", "Shipibo"], "lat": -9.20, "lon": -74.60, "ano": 2011, "escazu_pilar": "Participación ciudadana"},
        {"id": "pe-003", "titulo": "Ley 30215 - Mecanismos de Vigilancia", "estado": "revision", "tema": "Fiscalización ambiental", "ambito": "Nacional", "url": "https://www.minam.gob.pe/", "territorios_afectados": ["Shipibo"], "lat": -8.40, "lon": -74.55, "ano": 2014, "escazu_pilar": "Acceso a la información"},
        {"id": "pe-004", "titulo": "Decreto Supremo 004-2020", "estado": "activa", "tema": "Estándares de calidad", "ambito": "Nacional", "url": "https://www.minam.gob.pe/", "territorios_afectados": ["Asháninka"], "lat": -13.16, "lon": -72.55, "ano": 2020, "escazu_pilar": "Justicia ambiental"},
    ],
    'chile': [
        {"id": "cl-001", "titulo": "Ley 19.300 - Bases del Medio Ambiente", "estado": "activa", "tema": "Marco regulatorio", "ambito": "Nacional", "url": "https://www.bcn.cl/leychile/navegar?idNorma=30667", "territorios_afectados": ["Mapuche", "Rapa Nui"], "lat": -33.45, "lon": -70.67, "ano": 1994, "escazu_pilar": "Acceso a la información"},
        {"id": "cl-002", "titulo": "Ley 20.600 - Creación SEA", "estado": "activa", "tema": "Evaluación ambiental", "ambito": "Nacional", "url": "https://www.bcn.cl/leychile/navegar?idNorma=1034858", "territorios_afectados": ["Mapuche"], "lat": -38.74, "lon": -72.59, "ano": 2012, "escazu_pilar": "Participación ciudadana"},
        {"id": "cl-003", "titulo": "Ley 21.455 - Marco de Cambio Climático", "estado": "activa", "tema": "Acción climática", "ambito": "Nacional", "url": "https://www.bcn.cl/leychile/navegar?idNorma=1147349", "territorios_afectados": ["Mapuche", "Rapa Nui"], "lat": -27.11, "lon": -109.35, "ano": 2022, "escazu_pilar": "Justicia ambiental"},
        {"id": "cl-004", "titulo": "Ley 21.600 - Escazú ratificación", "estado": "activa", "tema": "Acuerdo Escazú", "ambito": "Nacional", "url": "https://www.bcn.cl/leychile/navegar?idNorma=1172020", "territorios_afectados": ["Mapuche"], "lat": -33.44, "lon": -70.65, "ano": 2023, "escazu_pilar": "Participación ciudadana"},
    ]
}

RESGUARDOS_DEMO = [
    {"nombre": "Nukak", "pueblo": "Nukak Makú", "departamento": "Guaviare", "pais": "Colombia", "lat": 2.50, "lon": -72.50, "habitantes": 600, "estado": "contacto_inicial", "normas_vinculadas": ["Ley 1523 de 2012", "Decreto 1076 de 2015"]},
    {"nombre": "Arhuaco", "pueblo": "Arhuaco", "departamento": "Cesar / Magdalena", "pais": "Colombia", "lat": 10.70, "lon": -73.65, "habitantes": 45000, "estado": "organizado", "normas_vinculadas": ["Ley 1955 de 2019", "Decreto 1076 de 2015"]},
    {"nombre": "Embera", "pueblo": "Emberá", "departamento": "Chocó / Antioquia", "pais": "Colombia", "lat": 6.00, "lon": -76.50, "habitantes": 25000, "estado": "organizado", "normas_vinculadas": ["Ley 1523 de 2012", "Ley 1955 de 2019"]},
    {"nombre": "Wayúu", "pueblo": "Wayúu", "departamento": "La Guajira", "pais": "Colombia", "lat": 11.50, "lon": -72.00, "habitantes": 380000, "estado": "organizado", "normas_vinculadas": ["Ley 1523 de 2012", "Ley 1955 de 2019"]},
    {"nombre": "Misak", "pueblo": "Misak / Guambiano", "departamento": "Cauca", "pais": "Colombia", "lat": 2.45, "lon": -76.60, "habitantes": 21000, "estado": "organizado", "normas_vinculadas": ["Decreto 1076 de 2015", "Decreto 2099 de 2021"]},
    {"nombre": "Asháninka", "pueblo": "Asháninka", "departamento": "Junín / Pasco", "pais": "Perú", "lat": -10.50, "lon": -74.50, "habitantes": 97000, "estado": "organizado", "normas_vinculadas": ["Ley 28611", "Ley 29785"]},
    {"nombre": "Awajún", "pueblo": "Awajún / Aguaruna", "departamento": "Amazonas", "pais": "Perú", "lat": -5.10, "lon": -78.20, "habitantes": 55000, "estado": "organizado", "normas_vinculadas": ["Ley 29785"]},
    {"nombre": "Shipibo", "pueblo": "Shipibo-Konibo", "departamento": "Ucayali", "pais": "Perú", "lat": -8.40, "lon": -74.55, "habitantes": 32000, "estado": "organizado", "normas_vinculadas": ["Ley 29785", "Ley 30215"]},
    {"nombre": "Mapuche", "pueblo": "Mapuche / Mapudungun", "departamento": "Araucanía / Bío Bío", "pais": "Chile", "lat": -38.74, "lon": -72.59, "habitantes": 1800000, "estado": "organizado", "normas_vinculadas": ["Ley 19.300", "Ley 20.600", "Ley 21.600"]},
    {"nombre": "Rapa Nui", "pueblo": "Rapa Nui", "departamento": "Isla de Pascua", "pais": "Chile", "lat": -27.11, "lon": -109.35, "habitantes": 7750, "estado": "organizado", "normas_vinculadas": ["Ley 19.300", "Ley 21.455"]},
]

ALERTAS_DEMO = [
    {"id": "alt-001", "fecha": "2026-08-10", "ubicacion": "Guaviare, Colombia", "lat": 2.50, "lon": -72.50, "severidad": "critica", "tipo": "deforestacion", "descripcion": "Alerta temprana de deforestación en territorio Nukak Makú. 12 hectáreas afectadas.", "normas_vinculadas": ["Ley 1523 de 2012", "Decreto 1076 de 2015"], "resguardos_afectados": ["Nukak"]},
    {"id": "alt-002", "fecha": "2026-08-08", "ubicacion": "Sierra Nevada, Colombia", "lat": 10.70, "lon": -73.65, "severidad": "alta", "tipo": "sequia", "descripcion": "Riesgo de sequía extrema en resguardos Arhuaco. Nivel hídrico crítico.", "normas_vinculadas": ["Ley 1955 de 2019"], "resguardos_afectados": ["Arhuaco"]},
    {"id": "alt-003", "fecha": "2026-08-05", "ubicacion": "La Guajira, Colombia", "lat": 11.50, "lon": -72.00, "severidad": "alta", "tipo": "contaminacion", "descripcion": "Contaminación por salinidad en acuíferos Wayúu. Afecta 3 comunidades.", "normas_vinculadas": ["Ley 1523 de 2012"], "resguardos_afectados": ["Wayúu"]},
    {"id": "alt-004", "fecha": "2026-08-12", "ubicacion": "Ucayali, Perú", "lat": -8.40, "lon": -74.55, "severidad": "critica", "tipo": "petroleo", "descripcion": "Derrame de petróleo en río Ucayali. Afecta pesca Shipibo-Konibo.", "normas_vinculadas": ["Ley 28611", "Ley 30215"], "resguardos_afectados": ["Shipibo"]},
    {"id": "alt-005", "fecha": "2026-08-01", "ubicacion": "Araucanía, Chile", "lat": -38.74, "lon": -72.59, "severidad": "media", "tipo": "incendio", "descripcion": "Incendio forestal cercano a comunidades Mapuche. Monitoreo activo.", "normas_vinculadas": ["Ley 19.300", "Ley 21.455"], "resguardos_afectados": ["Mapuche"]},
    {"id": "alt-006", "fecha": "2026-07-28", "ubicacion": "Chocó, Colombia", "lat": 6.00, "lon": -76.50, "severidad": "alta", "tipo": "mineria", "descripcion": "Minería ilegal detectada en cuenca del Atrato. Zona de reserva.", "normas_vinculadas": ["Decreto 1076 de 2015"], "resguardos_afectados": ["Embera"]},
]

ESTACIONES_DEMO = [
    {"id": "BOGT", "nombre": "Bogotá", "pais": "Colombia", "lat": 4.64, "lon": -74.08, "tipo": "GNSS"},
    {"id": "AREQ", "nombre": "Arequipa", "pais": "Perú", "lat": -16.40, "lon": -71.53, "tipo": "GNSS"},
    {"id": "SANT", "nombre": "Santiago", "pais": "Chile", "lat": -33.45, "lon": -70.66, "tipo": "GNSS"},
    {"id": "QUIT", "nombre": "Quito", "pais": "Ecuador", "lat": -0.18, "lon": -78.47, "tipo": "GNSS"},
    {"id": "LPBZ", "nombre": "La Paz", "pais": "Bolivia", "lat": -16.50, "lon": -68.15, "tipo": "GNSS"},
    {"id": "LIMA", "nombre": "Lima", "pais": "Perú", "lat": -12.05, "lon": -77.04, "tipo": "GNSS"},
]

# ============================================================
# FUNCIONES DE CARGA (JSON real o demo fallback)
# ============================================================
def cargar_json_o_demo(ruta, demo_data):
    try:
        base = os.path.join(os.path.dirname(__file__), '..', 'assets', 'geojson')
        with open(os.path.join(base, ruta), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return demo_data

def cargar_normas():
    return {
        'colombia': cargar_json_o_demo('normas_escazu_colombia.json', NORMAS_DEMO['colombia']),
        'peru': cargar_json_o_demo('normas_escazu_peru.json', NORMAS_DEMO['peru']),
        'chile': cargar_json_o_demo('normas_escazu_chile.json', NORMAS_DEMO['chile']),
    }

def cargar_alertas():
    return cargar_json_o_demo('alertas_escazu.json', ALERTAS_DEMO)

def cargar_resguardos():
    return cargar_json_o_demo('resguardos_indigenas.json', RESGUARDOS_DEMO)

def cargar_estaciones():
    return cargar_json_o_demo('estaciones_gnss.json', ESTACIONES_DEMO)

# ============================================================
# ESTILOS PERSONALIZADOS
# ============================================================
CUSTOM_CSS = """
<style>
    .andes-card { border-radius: 16px; border: 1px solid #e0e6d8; box-shadow: 0 4px 20px rgba(90,122,90,0.08); transition: transform 0.2s; }
    .andes-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(90,122,90,0.14); }
    .badge-activa { background: #d4edda; color: #155724; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .badge-revision { background: #fff3cd; color: #856404; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .badge-propuesta { background: #e2e3e5; color: #383d41; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
    .escazu-pill { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; margin-left: 6px; }
    .pill-info { background: #e8f4fd; color: #0c5460; }
    .pill-part { background: #fff3e0; color: #7c4a00; }
    .pill-just { background: #fce4ec; color: #880e4f; }
    .alerta-critica { border-left: 4px solid #dc3545; }
    .alerta-alta { border-left: 4px solid #fd7e14; }
    .alerta-media { border-left: 4px solid #ffc107; }
    .alerta-baja { border-left: 4px solid #28a745; }
    .resguardo-card { background: linear-gradient(135deg, #f8faf5 0%, #fff 100%); }
    .kpi-box { text-align: center; border-radius: 12px; font-weight: 600; font-size: 0.9rem; }
    .norma-link { color: #5a7a5a; text-decoration: none; font-weight: 500; }
    .norma-link:hover { color: #3d5a3d; text-decoration: underline; }
    .feed-item { padding: 12px 16px; background: white; border-radius: 12px; margin-bottom: 10px; border: 1px solid #f0ebe4; }
    .feed-item:hover { background: #fcfaf7; }
    .map-tooltip { font-size: 12px; }
    .escazu-indicator { text-align: center; padding: 16px; border-radius: 14px; background: white; border: 1px solid #e0e6d8; }
    .escazu-indicator i { font-size: 28px; margin-bottom: 8px; }
    .escazu-indicator .value { font-size: 24px; font-weight: 700; color: #5a7a5a; }
    .escazu-indicator .label { font-size: 12px; color: #8aa08a; margin-top: 4px; }
</style>
"""

# ============================================================
# COMPONENTES
# ============================================================
def create_banner():
    return dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/logo_andes.png", height="50px", className="me-3"),
            html.Div([
                html.I(className="fas fa-mountain me-2", style={"fontSize": "28px", "color": "#8aaa8a"}),
                html.Div([
                    html.H4("Andes Observatorio", className="text-white mb-0", style={"fontWeight": "700"}),
                    html.Small("Plataforma abierta para monitoreo geodésico y simulación de deformación · Región SIRGAS",
                              className="text-white-50")
                ])
            ], className="d-flex align-items-center me-auto"),
            dbc.Row([
                dbc.Col(html.Div(id="kpi-stations", className="kpi-box bg-success text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-normas", className="kpi-box bg-primary text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-alertas", className="kpi-box bg-warning text-dark p-2 rounded")),
                dbc.Col(html.Div(id="kpi-resguardos", className="kpi-box bg-info text-white p-2 rounded")),
            ], className="g-2")
        ], fluid=True),
        color="dark", dark=True, className="mb-4 py-3", style={"background": "linear-gradient(135deg, #2d4a2d 0%, #3d5a3d 100%)"}
    )

def create_escazu_indicators():
    normas = cargar_normas()
    total_normas = sum(len(v) for v in normas.values())
    activas = sum(1 for p in normas.values() for n in p if n.get('estado') == 'activa')
    revision = sum(1 for p in normas.values() for n in p if n.get('estado') == 'revision')

    # Contar por pilar Escazú
    info_count = sum(1 for p in normas.values() for n in p if n.get('escazu_pilar') == 'Acceso a la información')
    part_count = sum(1 for p in normas.values() for n in p if n.get('escazu_pilar') == 'Participación ciudadana')
    just_count = sum(1 for p in normas.values() for n in p if n.get('escazu_pilar') == 'Justicia ambiental')

    return dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-book-open", style={"color": "#2980b9"}),
                html.Div(f"{info_count}", className="value"),
                html.Div("Acceso a la información", className="label")
            ], className="escazu-indicator")
        ], width=4),
        dbc.Col([
            html.Div([
                html.I(className="fas fa-users", style={"color": "#e67e22"}),
                html.Div(f"{part_count}", className="value"),
                html.Div("Participación ciudadana", className="label")
            ], className="escazu-indicator")
        ], width=4),
        dbc.Col([
            html.Div([
                html.I(className="fas fa-gavel", style={"color": "#c0392b"}),
                html.Div(f"{just_count}", className="value"),
                html.Div("Justicia ambiental", className="label")
            ], className="escazu-indicator")
        ], width=4),
    ], className="mb-4")

def create_mapa():
    estaciones = cargar_estaciones()
    resguardos = cargar_resguardos()
    alertas = cargar_alertas()
    normas = cargar_normas()

    fig = go.Figure()

    # Capa: Estaciones GNSS
    fig.add_trace(go.Scattergeo(
        lon=[e['lon'] for e in estaciones],
        lat=[e['lat'] for e in estaciones],
        mode='markers+text',
        marker=dict(size=12, color='#2980b9', symbol='diamond', line=dict(width=2, color='white')),
        text=[e['id'] for e in estaciones],
        textposition="top center",
        name='🛰️ Estaciones GNSS',
        hovertemplate='<b>%{text}</b><br>País: %{customdata}<extra></extra>',
        customdata=[e['pais'] for e in estaciones]
    ))

    # Capa: Resguardos indígenas
    fig.add_trace(go.Scattergeo(
        lon=[r['lon'] for r in resguardos],
        lat=[r['lat'] for r in resguardos],
        mode='markers',
        marker=dict(size=16, color='#27ae60', symbol='circle', opacity=0.7, line=dict(width=2, color='#1e8449')),
        name='🏕️ Resguardos indígenas',
        hovertemplate='<b>%{customdata}</b><br>Pueblo: %{text}<br>Hab: %{marker.size:,}<extra></extra>',
        text=[r['pueblo'] for r in resguardos],
        customdata=[r['nombre'] for r in resguardos]
    ))

    # Capa: Alertas
    colores_alerta = {'critica': '#dc3545', 'alta': '#fd7e14', 'media': '#ffc107', 'baja': '#28a745'}
    for sev in ['critica', 'alta', 'media', 'baja']:
        alt_sev = [a for a in alertas if a.get('severidad') == sev]
        if alt_sev:
            fig.add_trace(go.Scattergeo(
                lon=[a['lon'] for a in alt_sev],
                lat=[a['lat'] for a in alt_sev],
                mode='markers',
                marker=dict(size=14, color=colores_alerta[sev], symbol='triangle-up', opacity=0.9, line=dict(width=2, color='white')),
                name=f'⚠️ Alerta {sev}',
                hovertemplate='<b>%{customdata}</b><br>%{text}<br>Tipo: %{marker.color}<extra></extra>',
                text=[a['descripcion'][:80] + '...' for a in alt_sev],
                customdata=[a['ubicacion'] for a in alt_sev]
            ))

    # Capa: Normas (puntos más pequeños, semi-transparentes)
    all_normas = []
    for pais, lista in normas.items():
        for n in lista:
            n['pais'] = pais
            all_normas.append(n)

    fig.add_trace(go.Scattergeo(
        lon=[n.get('lon', 0) for n in all_normas if n.get('lon')],
        lat=[n.get('lat', 0) for n in all_normas if n.get('lat')],
        mode='markers',
        marker=dict(size=8, color='#8e44ad', symbol='square', opacity=0.6),
        name='📜 Normas ambientales',
        hovertemplate='<b>%{customdata}</b><br>%{text}<br>Estado: %{marker.color}<extra></extra>',
        text=[n['tema'] for n in all_normas if n.get('lat')],
        customdata=[n['titulo'] for n in all_normas if n.get('lat')]
    ))

    fig.update_layout(
        geo=dict(
            scope='south america',
            showland=True,
            landcolor='#f5f5dc',
            showcountries=True,
            countrycolor='#cccccc',
            showocean=True,
            oceancolor='#e8f4f8',
            showlakes=True,
            lakecolor='#d4e6f1',
            showrivers=True,
            rivercolor='#d4e6f1',
            center=dict(lat=-15, lon=-65),
            projection_scale=3.5,
            bgcolor='#f8f5f0'
        ),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.9)"),
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor='#f8f5f0',
        plot_bgcolor='#f8f5f0',
        height=550
    )
    return fig

def create_feed_alertas():
    alertas = cargar_alertas()
    items = []
    for a in alertas:
        sev_class = f"alerta-{a.get('severidad', 'media')}"
        icono = {'critica': '🔴', 'alta': '🟠', 'media': '🟡', 'baja': '🟢'}.get(a.get('severidad'), '⚪')
        resguardo_links = []
        for r in a.get('resguardos_afectados', []):
            resguardo_links.append(html.A(r, href="#", className="me-2 text-decoration-none", style={"color": "#5a7a5a", "fontWeight": "600"}))

        norma_badges = []
        for n in a.get('normas_vinculadas', []):
            norma_badges.append(html.Span(n, className="badge-revision me-1 mb-1", style={"fontSize": "10px"}))

        items.append(html.Div([
            html.Div([
                html.Span(f"{icono} {a['fecha']}", className="fw-bold me-2"),
                html.Span(a['ubicacion'], className="text-muted small")
            ]),
            html.P(a['descripcion'], className="mb-1 mt-1", style={"fontSize": "13px"}),
            html.Div([
                html.Small("Resguardos: ", className="text-muted"),
                html.Span(resguardo_links)
            ], className="mb-1") if resguardo_links else None,
            html.Div(norma_badges) if norma_badges else None,
        ], className=f"feed-item {sev_class}"))
    return items

def create_normas_cards(pais_filtro=None, pilar_filtro=None):
    normas = cargar_normas()
    cards = []
    for pais, lista in normas.items():
        if pais_filtro and pais != pais_filtro:
            continue
        for n in lista:
            if pilar_filtro and n.get('escazu_pilar') != pilar_filtro:
                continue
            estado_badge = {
                'activa': html.Span('● Activa', className='badge-activa'),
                'revision': html.Span('● En revisión', className='badge-revision'),
                'propuesta': html.Span('● Propuesta', className='badge-propuesta')
            }.get(n.get('estado'), html.Span('● ' + n.get('estado', ''), className='badge-propuesta'))

            pilar_class = {
                'Acceso a la información': 'pill-info',
                'Participación ciudadana': 'pill-part',
                'Justicia ambiental': 'pill-just'
            }.get(n.get('escazu_pilar'), 'pill-info')

            territorios = html.Div([
                html.Small("Territorios: ", className="text-muted"),
                html.Span(", ".join(n.get('territorios_afectados', [])), className="small fw-semibold", style={"color": "#5a7a5a"})
            ]) if n.get('territorios_afectados') else None

            cards.append(dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6(n['titulo'], className="card-title mb-1", style={"fontSize": "14px", "fontWeight": "700", "color": "#2d4a2d"}),
                        html.A(html.I(className="fas fa-external-link-alt ms-2", style={"fontSize": "11px", "color": "#8aa08a"}),
                               href=n.get('url', '#'), target="_blank", title="Ver norma")
                    ], className="d-flex justify-content-between align-items-start"),
                    html.P(n['tema'], className="card-text mb-2", style={"fontSize": "12px", "color": "#666"}),
                    html.Div([
                        estado_badge,
                        html.Span(n.get('escazu_pilar', ''), className=f"escazu-pill {pilar_class}")
                    ], className="mb-2"),
                    territorios,
                    html.Div([
                        html.Small(f"📍 {n.get('ambito', 'Nacional')} · 📅 {n.get('ano', '')}", className="text-muted", style={"fontSize": "11px"})
                    ], className="mt-2")
                ], style={"padding": "14px"})
            ], className="andes-card mb-3"))
    return cards

def create_resguardos_list():
    resguardos = cargar_resguardos()
    items = []
    for r in resguardos:
        estado_color = {"contacto_inicial": "#dc3545", "organizado": "#28a745", "en_proceso": "#ffc107"}
        estado_label = {"contacto_inicial": "Contacto inicial", "organizado": "Organizado", "en_proceso": "En proceso"}

        norma_links = []
        for n in r.get('normas_vinculadas', []):
            norma_links.append(html.Span(n, className="badge-activa me-1 mb-1", style={"fontSize": "10px"}))

        items.append(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H6(r['nombre'], className="mb-0", style={"fontWeight": "700", "color": "#2d4a2d"}),
                    html.Span(estado_label.get(r.get('estado', ''), r.get('estado', '')), 
                             style={"fontSize": "11px", "color": estado_color.get(r.get('estado'), '#666'), "fontWeight": "600"})
                ], className="d-flex justify-content-between align-items-center mb-2"),
                html.P(f"Pueblo: {r['pueblo']} · {r['departamento']}, {r['pais']}", className="mb-1", style={"fontSize": "12px", "color": "#666"}),
                html.P(f"👥 {r.get('habitantes', 'N/D'):,} habitantes · 📍 {r['lat']:.2f}, {r['lon']:.2f}", 
                      className="mb-2", style={"fontSize": "11px", "color": "#888"}),
                html.Div([
                    html.Small("Normas vinculadas: ", className="text-muted me-1"),
                    html.Div(norma_links, className="d-inline-flex flex-wrap")
                ]) if norma_links else None,
            ], style={"padding": "14px"})
        ], className="andes-card resguardo-card mb-2"))
    return items

# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
app.layout = dbc.Container([
    html.Link(rel="stylesheet", href="/assets/custom.css"),
    create_banner(),

    dcc.Interval(id='interval-refresh', interval=60*1000),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("🏔️ Bienvenido a Andes Observatorio")),
        dbc.ModalBody([
            html.P("Esta plataforma integra datos geodésicos (SIRGAS), normativas ambientales y territorios indígenas para el monitoreo de la Región Andina."),
            html.Hr(),
            html.P([html.Strong("1. Mapa Principal: "), "Explora estaciones GNSS, resguardos indígenas, alertas y normas georreferenciadas."]),
            html.P([html.Strong("3. MAM Escazú: "), "Vincula alertas ambientales con normas y territorios vulnerables bajo el Marco Escazú."]),
            html.Hr(),
            html.P("💡 Pasa el cursor sobre los elementos del mapa para ver el tooltip 'Ley en el Territorio'.", className="text-muted small")
        ]),
        dbc.ModalFooter(dbc.Button("Entendido", id="close-onboarding", className="ms-auto", color="success"))
    ], id="onboarding-modal", is_open=True, backdrop=True),

    dbc.Tabs([
        # ============================================================
        # TAB 1: MAPA PRINCIPAL
        # ============================================================
        dbc.Tab(label="🗺️ Mapa Principal", tab_id="tab-map", children=[
            html.Div([
                html.H4("Mapa Interactivo Andino", className="mt-4 mb-3", style={"color": "#5a7a5a", "fontWeight": "700"}),
                html.P("Visualización integrada de estaciones GNSS, territorios indígenas, alertas ambientales y normativas georreferenciadas.", 
                       className="text-muted mb-3"),
                dbc.Row([
                    dbc.Col([
                        dcc.Graph(id='mapa-principal', figure=create_mapa(), config={'displayModeBar': True})
                    ], width=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H5("📊 Leyenda del mapa", className="mt-3 mb-2"),
                        html.Div([
                            html.Span("🛰️ ", className="me-1"), html.Small("Estaciones GNSS", className="me-3"),
                            html.Span("🏕️ ", className="me-1"), html.Small("Resguardos indígenas", className="me-3"),
                            html.Span("🔴 ", className="me-1"), html.Small("Alerta crítica", className="me-3"),
                            html.Span("🟠 ", className="me-1"), html.Small("Alerta alta", className="me-3"),
                            html.Span("📜 ", className="me-1"), html.Small("Normas ambientales"),
                        ], className="p-3 rounded", style={"background": "#fcfaf7", "border": "1px solid #ede8e0"})
                    ], width=12)
                ], className="mt-2 mb-4")
            ])
        ]),

        # ============================================================
        # TAB 2: DASHBOARD DE SERIES
        # ============================================================

        # ============================================================
        # TAB 3: MAM ESCAZÚ (MEJORADO)
        # ============================================================
        dbc.Tab(label="🚦 MAM Escazú", tab_id="tab-mame", children=[
            html.Div([
                html.H3("Monitoreo Ambiental con Marco Escazú", className="mt-4 mb-2", style={"color": "#5a7a5a", "fontWeight": "700"}),
                html.P("Vinculación de alertas ambientales con normas georreferenciadas, territorios vulnerables y los tres pilares del Acuerdo de Escazú.",
                       className="text-muted mb-4"),

                # Indicadores Escazú
                create_escazu_indicators(),

                dbc.Row([
                    # Columna 1: Semáforo + Normas
                    dbc.Col([
                        html.H5("📋 Normas Ambientales por País", className="mb-3"),
                        dbc.Row([
                            dbc.Col(dbc.Select(id='filtro-pais-normas', options=[
                                {'label': 'Todos los países', 'value': ''},
                                {'label': '🇨🇴 Colombia', 'value': 'colombia'},
                                {'label': '🇵🇪 Perú', 'value': 'peru'},
                                {'label': '🇨🇱 Chile', 'value': 'chile'}
                            ], value=''), width=6),
                            dbc.Col(dbc.Select(id='filtro-pilar-normas', options=[
                                {'label': 'Todos los pilares', 'value': ''},
                                {'label': 'Acceso a la información', 'value': 'Acceso a la información'},
                                {'label': 'Participación ciudadana', 'value': 'Participación ciudadana'},
                                {'label': 'Justicia ambiental', 'value': 'Justicia ambiental'}
                            ], value=''), width=6),
                        ], className="mb-3"),
                        html.Div(id='normas-container', children=create_normas_cards())
                    ], width=4),

                    # Columna 2: Feed de Alertas
                    dbc.Col([
                        html.H5("⚠️ Feed de Alertas Ambientales", className="mb-3"),
                        html.Div(id='alertas-feed-container', children=create_feed_alertas(), 
                                style={"maxHeight": "600px", "overflowY": "auto", "paddingRight": "8px"})
                    ], width=4),

                    # Columna 3: Resguardos Indígenas
                    dbc.Col([
                        html.H5("🏕️ Territorios Indígenas Monitoreados", className="mb-3"),
                        html.Div(id='resguardos-container', children=create_resguardos_list(),
                                style={"maxHeight": "600px", "overflowY": "auto", "paddingRight": "8px"})
                    ], width=4),
                ])
            ])
        ]),

        # ============================================================
        # TAB 4: SIMULADOR
        # ============================================================
    ])
], fluid=True, style={"background": "#f8f5f0", "minHeight": "100vh", "paddingBottom": "40px"})

# ============================================================
# CALLBACKS
# ============================================================

# --- KPIs ---
@app.callback(
    [Output("kpi-stations", "children"),
     Output("kpi-normas", "children"),
     Output("kpi-alertas", "children"),
     Output("kpi-resguardos", "children")],
    Input("interval-refresh", "n_intervals")
)
def update_kpis(n):
    normas = cargar_normas()
    alertas = cargar_alertas()
    resguardos = cargar_resguardos()
    estaciones = cargar_estaciones()
    n_normas = sum(len(v) for v in normas.values())
    n_alertas_criticas = sum(1 for a in alertas if a.get('severidad') == 'critica')
    return (
        html.Div([html.Div(f"{len(estaciones)}", style={"fontSize": "20px", "fontWeight": "700"}), html.Div("Estaciones GNSS", style={"fontSize": "11px"})]),
        html.Div([html.Div(f"{n_normas}", style={"fontSize": "20px", "fontWeight": "700"}), html.Div("Normas activas", style={"fontSize": "11px"})]),
        html.Div([html.Div(f"{n_alertas_criticas}", style={"fontSize": "20px", "fontWeight": "700", "color": "#fff3cd"}), html.Div("Alertas críticas", style={"fontSize": "11px"})]),
        html.Div([html.Div(f"{len(resguardos)}", style={"fontSize": "20px", "fontWeight": "700"}), html.Div("Resguardos", style={"fontSize": "11px"})]),
    )

# --- Onboarding ---
@app.callback(
    Output("onboarding-modal", "is_open"),
    Input("close-onboarding", "n_clicks"),
    prevent_initial_call=True
)
def close_onboarding(n):
    return False

# --- Filtro de normas ---
@app.callback(
    Output('normas-container', 'children'),
    [Input('filtro-pais-normas', 'value'),
     Input('filtro-pilar-normas', 'value')]
)
def filtrar_normas(pais, pilar):
    return create_normas_cards(pais_filtro=pais if pais else None, pilar_filtro=pilar if pilar else None)


if __name__ == '__main__':
    app.run(debug=True, port=8051)
