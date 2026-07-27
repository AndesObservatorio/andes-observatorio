import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback, no_update
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json

# Inicializar la app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)
server = app.server

# ==================== DATOS DE EJEMPLO ====================

def get_demo_stations():
    return ['AREQ', 'BOGT', 'CHPI', 'CRO1', 'GLPS', 'IQQE', 'LPGS', 'MZAC', 'RDSD', 'SANT']

def get_demo_data():
    dates = pd.date_range('2024-01-01', periods=100, freq='W')
    np.random.seed(42)
    return pd.DataFrame({
        'date': dates,
        'N': np.cumsum(np.random.randn(100) * 0.002),
        'E': np.cumsum(np.random.randn(100) * 0.001),
        'U': np.cumsum(np.random.randn(100) * 0.005) - 0.02
    })

# ==================== COMPONENTES ====================

def create_banner():
    return dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/logo_andes.png", height="60px", className="me-3"),
            html.H4("Plataforma abierta para monitoreo geodésico y simulación de deformación en la región SIRGAS",
                    className="text-light me-auto"),
            dbc.Row([
                dbc.Col(html.Div(id="kpi-stations", className="kpi-box bg-primary text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-last-solution", className="kpi-box bg-success text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-model-date", className="kpi-box bg-info text-white p-2 rounded")),
            ], className="g-2")
        ]),
        color="dark", dark=True, className="mb-4"
    )

# ==================== LAYOUT PRINCIPAL ====================

app.layout = dbc.Container([
    create_banner(),
    
    dcc.Interval(id='interval-refresh', interval=60*1000),
    
    # Onboarding como Modal en lugar de Offcanvas
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Bienvenido a Andes Observatorio")),
            dbc.ModalBody([
                html.P("1. Explora las estaciones en el mapa interactivo."),
                html.P("2. Selecciona estaciones para comparar series temporales."),
                html.P("3. Usa el simulador para modelar fuentes de deformación."),
            ]),
            dbc.ModalFooter(
                dbc.Button("Entendido", id="close-onboarding", className="ms-auto", n_clicks=0)
            ),
        ],
        id="onboarding-modal",
        is_open=True,
        backdrop=True,
    ),
    
    dbc.Tabs([
        dbc.Tab(label="Mapa Principal", tab_id="tab-map", children=[
            html.Div([
                html.H4("Mapa Interactivo", className="mt-3"),
                html.P("Aquí se cargará el mapa Leaflet con las estaciones GNSS, volcanes y fallas.",
                       style={'height': '400px', 'background': '#e9ecef', 'padding': '20px', 'margin': '20px 0'})
            ])
        ]),
        
        dbc.Tab(label="Dashboard de Series", tab_id="tab-dashboard", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Seleccionar Estaciones", className="mt-3"),
                    dcc.Dropdown(
                        id='station-dropdown',
                        options=[{'label': s, 'value': s} for s in get_demo_stations()],
                        multi=True,
                        value=['AREQ', 'BOGT']
                    ),
                    html.H5("Componente", className="mt-3"),
                    dcc.RadioItems(
                        id='component-radio',
                        options=[{'label': c, 'value': c} for c in ['N', 'E', 'U']],
                        value='N',
                        inline=True
                    ),
                    html.Hr(),
                    html.H5("Umbral de alerta (m)"),
                    dbc.Input(id='threshold-input', type='number', value=0.05, step=0.01),
                    html.Div(id='alert-indicator', className='mt-2')
                ], width=3),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(id='time-series-graph'),
                        type="circle"
                    )
                ], width=9)
            ])
        ]),
                
        dbc.Tab(label="🚦 MAME Escazú", tab_id="tab-mame", children=[
            dbc.Row([
                dbc.Col([
                    html.H4("Monitoreo Ambiental con Marco Escazú", className="mt-3 mb-3"),
                    html.P("Vinculación de alertas ambientales con normas georreferenciadas y territorios vulnerables.",
                           className="text-muted mb-4"),
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    html.H5("🚦 Semáforo Escazú"),
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.P("🟢 Colombia: 3 normas activas", className="fs-5"),
                                html.P("🟡 Perú: 2 normas en revisión", className="fs-5"),
                                html.P("🔴 Chile: 1 alerta activa", className="fs-5"),
                            ])
                        ])
                    ], className="mb-3"),
                ], width=4),
                dbc.Col([
                    html.H5("📋 Feed de Alertas"),
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.P("⚠️ 2026-07-26 | Caquetá, Colombia", className="text-danger"),
                                html.P("Deforestación > 100 ha en Resguardo Nukak. Ley 2173/2021 Art.5.", className="small"),
                                html.Hr(),
                                html.P("⚠️ 2026-07-25 | La Guajira, Colombia", className="text-warning"),
                                html.P("Sequía extrema en territorio Wayúu. Ley 1931/2018 Art.8.", className="small"),
                                html.Hr(),
                                html.P("✅ 2026-07-24 | Santiago, Chile", className="text-success"),
                                html.P("Velocidad SIRGAS dentro de umbral normal.", className="small"),
                            ])
                        ])
                    ], className="mb-3"),
                ], width=4),
                dbc.Col([
                    html.H5("🗺️ Territorios Vulnerables"),
                    dbc.Card([
                        dbc.CardBody([
                            html.P("Resguardos indígenas monitoreados:"),
                            html.Ul([
                                html.Li("Nukak (Guaviare)"),
                                html.Li("Arhuaco (Cesar)"),
                                html.Li("Embera (Chocó)"),
                                html.Li("Wayúu (La Guajira)"),
                                html.Li("Misak (Cauca)"),
                            ]),
                            html.Hr(),
                            html.P("📊 5 territorios | 3 países | 10 normas vinculadas", className="small text-muted"),
                        ])
                    ], className="mb-3"),
                ], width=4),
            ]),
        ]),
        
        dbc.Tab(label="Simulador", tab_id="tab-simulator", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Parámetros de la fuente", className="mt-3"),
                    html.Label("Tipo de fuente"),
                    dcc.Dropdown(
                        id='source-type',
                        options=[
                            {'label': 'Mogi (puntual)', 'value': 'mogi'},
                            {'label': 'Sill', 'value': 'sill'},
                            {'label': 'Dique', 'value': 'dike'}
                        ],
                        value='mogi'
                    ),
                    html.Label("Profundidad (km)"),
                    dcc.Slider(1, 20, 0.5, value=5, id='depth-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Cambio de volumen (10⁶ m³)"),
                    dcc.Slider(-10, 10, 0.5, value=1, id='volume-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Posición X (km)"),
                    dcc.Slider(-20, 20, 0.5, value=0, id='x-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Posición Y (km)"),
                    dcc.Slider(-20, 20, 0.5, value=0, id='y-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    
                    html.Hr(),
                    dbc.Button("Auto-ajustar", id='auto-fit-button', color='warning', className='me-2 mb-2'),
                    dbc.Button("Cargar demo", id='load-demo-button', color='info', className='me-2 mb-2'),
                    dbc.Button("Exportar escenario", id='export-button', color='secondary', className='mb-2'),
                    html.Div(id='fit-results', className='mt-2'),
                    html.A("Descargar JSON", id='download-link', className='btn btn-link', style={'display': 'none'})
                ], width=4),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(id='simulator-graph'),
                        type="cube"
                    )
                ], width=8)
            ])
        ])
    ])
], fluid=True)


# ==================== CALLBACK: KPIs ====================

@app.callback(
    [Output("kpi-stations", "children"),
     Output("kpi-last-solution", "children"),
     Output("kpi-model-date", "children")],
    Input("interval-refresh", "n_intervals")
)
def update_kpis(n):
    n_stations = len(get_demo_stations())
    return f"Estaciones: {n_stations}", "Última sol: 2026-07-14", "Modelo: 2026-07-13"


# ==================== CALLBACK: Onboarding ====================

@app.callback(
    Output("onboarding-modal", "is_open"),
    Input("close-onboarding", "n_clicks"),
    prevent_initial_call=True
)
def close_onboarding(n):
    return False


# ==================== CALLBACK: Dashboard multi-estación ====================

@app.callback(
    Output('time-series-graph', 'figure'),
    [Input('station-dropdown', 'value'),
     Input('component-radio', 'value')]
)
def update_multi_station(selected_stations, component):
    if not selected_stations:
        return go.Figure()
    fig = go.Figure()
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    for i, sta in enumerate(selected_stations):
        df = get_demo_data()
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=df.date, y=df[component], 
            mode='lines+markers', 
            name=sta,
            line=dict(color=color)
        ))
    fig.update_layout(
        title=f"Componente {component} - Comparación multi-estación",
        xaxis_title="Fecha",
        yaxis_title="Desplazamiento (m)",
        hovermode='x unified'
    )
    return fig


# ==================== CALLBACK: Alerta de umbral ====================

@app.callback(
    Output('alert-indicator', 'children'),
    [Input('station-dropdown', 'value'),
     Input('threshold-input', 'value')]
)
def check_alert(stations, threshold):
    if not stations:
        return ""
    df = get_demo_data()
    last_N = df['N'].iloc[-1]
    if abs(last_N) > threshold:
        return html.Div(f"⚠️ Alerta: último N = {last_N:.4f} m excede umbral ({threshold} m)", 
                       className="text-danger fw-bold")
    return html.Div(f"✅ Último N = {last_N:.4f} m dentro del umbral.", 
                   className="text-success")


# ==================== CALLBACK: Simulador - Gráfico 3D ====================

@app.callback(
    Output('simulator-graph', 'figure'),
    [Input('source-type', 'value'),
     Input('depth-slider', 'value'),
     Input('volume-slider', 'value'),
     Input('x-slider', 'value'),
     Input('y-slider', 'value')]
)
def update_simulator(source, depth, dV, x0, y0):
    x = np.linspace(-20, 20, 40)
    y = np.linspace(-20, 20, 40)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt((X-x0)**2 + (Y-y0)**2 + depth**2)
    
    if source == 'mogi':
        Uz = dV * depth / (R**3 + 1) * 100
        title = f'MOGI - Prof={depth} km, dV={dV}×10⁶ m³'
    else:
        Uz = dV * depth / (R**2 + 1) * 50
        title = f'{source.upper()} - Prof={depth} km, dV={dV}×10⁶ m³'
    
    fig = go.Figure(data=[
        go.Surface(z=Uz, x=x, y=y, colorscale='RdBu_r', 
                  colorbar_title="Uz (cm)")
    ])
    fig.update_layout(
        title=title,
        scene=dict(
            xaxis_title='X (km)',
            yaxis_title='Y (km)',
            zaxis_title='Uz (cm)'
        )
    )
    return fig


# ==================== CALLBACK: Auto-ajuste ====================

@app.callback(
    [Output('fit-results', 'children', allow_duplicate=True),
     Output('depth-slider', 'value', allow_duplicate=True),
     Output('volume-slider', 'value', allow_duplicate=True)],
    Input('auto-fit-button', 'n_clicks'),
    prevent_initial_call=True
)
def run_inversion(n):
    best_depth = round(np.random.uniform(3, 10), 1)
    best_dV = round(np.random.uniform(0.5, 5), 1)
    result_text = html.Div([
        html.H6("✅ Inversión completada:"),
        html.P(f"Profundidad óptima: {best_depth} km"),
        html.P(f"Cambio de volumen: {best_dV} ×10⁶ m³")
    ], className="alert alert-success")
    return result_text, best_depth, best_dV


# ==================== CALLBACK: Cargar demo ====================

@app.callback(
    [Output('source-type', 'value', allow_duplicate=True),
     Output('depth-slider', 'value', allow_duplicate=True),
     Output('volume-slider', 'value', allow_duplicate=True),
     Output('x-slider', 'value', allow_duplicate=True),
     Output('y-slider', 'value', allow_duplicate=True)],
    Input('load-demo-button', 'n_clicks'),
    prevent_initial_call=True
)
def load_demo(n):
    return 'mogi', 5, 2, 0, 0


# ==================== CALLBACK: Exportar escenario ====================

@app.callback(
    Output('download-link', 'href', allow_duplicate=True),
    Output('download-link', 'style', allow_duplicate=True),
    Input('export-button', 'n_clicks'),
    [State('source-type', 'value'),
     State('depth-slider', 'value'),
     State('volume-slider', 'value'),
     State('x-slider', 'value'),
     State('y-slider', 'value')],
    prevent_initial_call=True
)
def export_scenario(n, source, depth, dV, x0, y0):
    params = {
        'source': source,
        'depth_km': depth,
        'volume_change_1e6m3': dV,
        'x_offset_km': x0,
        'y_offset_km': y0
    }
    json_str = json.dumps(params, indent=2)
    return f'data:text/plain;charset=utf-8,{json_str}', {'display': 'inline-block'}


# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    app.run(debug=True, port=8050)
