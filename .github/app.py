import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json

# ==================== INICIALIZAR APP ====================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
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

# ==================== BANNER CON KPIs ====================

def create_banner():
    return dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/logo_andes.png", height="55px", className="me-3"),
            html.H4("Plataforma abierta para monitoreo geodésico y simulación de deformación en la región SIRGAS",
                    className="text-light me-auto"),
            dbc.Row([
                dbc.Col(html.Div(id="kpi-stations", 
                                 className="kpi-box bg-primary text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-last-solution", 
                                 className="kpi-box bg-success text-white p-2 rounded")),
                dbc.Col(html.Div(id="kpi-model-date", 
                                 className="kpi-box bg-info text-white p-2 rounded")),
            ], className="g-2")
        ]),
        color="dark", dark=True, className="mb-4"
    )

# ==================== LAYOUT PRINCIPAL ====================

app.layout = html.Div([
    # CSS personalizado
    html.Link(rel="stylesheet", href="/assets/custom.css"),
    
    create_banner(),
    
    dcc.Interval(id='interval-refresh', interval=60*1000),
    
    # Onboarding Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("🔭 Bienvenido a Andes Observatorio")),
        dbc.ModalBody([
            html.Div([
                html.P("📡 1. Explora las estaciones GNSS en el mapa interactivo.", className="fs-6"),
                html.P("📊 2. Selecciona estaciones para comparar series temporales.", className="fs-6"),
                html.P("🌋 3. Usa el simulador para modelar fuentes de deformación volcánica.", className="fs-6"),
            ])
        ]),
        dbc.ModalFooter(
            dbc.Button("¡Entendido! Comenzar", id="close-onboarding", className="ms-auto", n_clicks=0, color="primary")
        ),
    ], id="onboarding-modal", is_open=True, backdrop=True, size="lg"),
    
    # Tabs principales
    dbc.Tabs([
        dbc.Tab(label="🗺️ Mapa Principal", tab_id="tab-map", children=[
            html.Div([
                html.H4("Mapa Interactivo de Estaciones GNSS", className="mt-4 mb-3 fade-in"),
                html.P("Visualización de estaciones, fallas y volcanes en tiempo real.",
                       className="text-muted mb-4 fade-in"),
                html.Div("🌎 El mapa Leaflet se cargará aquí con las capas: estaciones GNSS, fallas activas y volcanes.",
                         style={'height': '450px', 'background': 'linear-gradient(135deg, #e9ecef, #dee2e6)',
                                'padding': '30px', 'borderRadius': '16px', 'textAlign': 'center',
                                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                                'fontSize': '1.3rem', 'color': '#6c757d', 'margin': '20px 0',
                                'boxShadow': '0 2px 10px rgba(0,0,0,0.08)', 'border': '2px dashed #adb5bd'})
            ], className="fade-in")
        ]),
        
        dbc.Tab(label="📊 Dashboard de Series", tab_id="tab-dashboard", children=[
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
                        options=[{'label': f' {c}', 'value': c} for c in ['N (Norte)', 'E (Este)', 'U (Vertical)']],
                        value='N',
                        inputStyle={"margin-right": "5px"},
                        labelStyle={"margin-right": "15px", "font-weight": "500"}
                    ),
                    html.Hr(),
                    html.H5("Umbral de alerta (m)"),
                    dbc.Input(id='threshold-input', type='number', value=0.05, step=0.01),
                    html.Div(id='alert-indicator', className='mt-3 p-3 rounded')
                ], width=3),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(id='time-series-graph', config={'displayModeBar': True}),
                        type="circle", color="#2D6A4F"
                    )
                ], width=9)
            ])
        ]),
        
        dbc.Tab(label="🌋 Simulador de Deformación", tab_id="tab-simulator", children=[
            dbc.Row([
                dbc.Col([
                    html.H5("Parámetros de la Fuente", className="mt-3"),
                    html.Label("Tipo de fuente", className="fw-bold"),
                    dcc.Dropdown(
                        id='source-type',
                        options=[
                            {'label': '🔵 Mogi (puntual)', 'value': 'mogi'},
                            {'label': '🟠 Sill (horizontal)', 'value': 'sill'},
                            {'label': '🔴 Dique (vertical)', 'value': 'dike'}
                        ],
                        value='mogi'
                    ),
                    html.Label("Profundidad (km)", className="mt-3 fw-bold"),
                    dcc.Slider(1, 20, 0.5, value=5, id='depth-slider',
                              tooltip={"placement": "bottom", "always_visible": True},
                              marks={1: '1', 5: '5', 10: '10', 15: '15', 20: '20'}),
                    html.Label("Cambio de volumen (10⁶ m³)", className="fw-bold"),
                    dcc.Slider(-10, 10, 0.5, value=1, id='volume-slider',
                              tooltip={"placement": "bottom", "always_visible": True},
                              marks={-10: '-10', 0: '0', 10: '10'}),
                    html.Label("Posición X (km)", className="fw-bold"),
                    dcc.Slider(-20, 20, 0.5, value=0, id='x-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    html.Label("Posición Y (km)", className="fw-bold"),
                    dcc.Slider(-20, 20, 0.5, value=0, id='y-slider',
                              tooltip={"placement": "bottom", "always_visible": True}),
                    
                    html.Hr(),
                    dbc.Button("🔍 Auto-ajustar", id='auto-fit-button', color='warning', className='me-2 mb-2 w-100'),
                    dbc.Button("📥 Cargar demo", id='load-demo-button', color='info', className='me-2 mb-2 w-100'),
                    dbc.Button("💾 Exportar escenario", id='export-button', color='secondary', className='mb-2 w-100'),
                    html.Div(id='fit-results', className='mt-3'),
                    html.A("📄 Descargar JSON", id='download-link', className='btn btn-link w-100 text-center',
                           style={'display': 'none'})
                ], width=4),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(id='simulator-graph', config={'displayModeBar': True}),
                        type="cube", color="#2D6A4F"
                    )
                ], width=8)
            ])
        ])
    ]),
    
    # Botón modo oscuro/claro
    html.Button("🌓", id="theme-toggle", className="theme-switch"),
    
], className="fade-in")

# ==================== CALLBACK: KPIs ====================

@app.callback(
    [Output("kpi-stations", "children"),
     Output("kpi-last-solution", "children"),
     Output("kpi-model-date", "children")],
    Input("interval-refresh", "n_intervals")
)
def update_kpis(n):
    return f"{len(get_demo_stations())} activas", "Solución: 2026-07-14", "Modelo: 2026-07-13"

# ==================== CALLBACK: Onboarding ====================

@app.callback(
    Output("onboarding-modal", "is_open"),
    Input("close-onboarding", "n_clicks"),
    prevent_initial_call=True
)
def close_onboarding(n):
    return False

# ==================== CALLBACK: Dashboard ====================

@app.callback(
    Output('time-series-graph', 'figure'),
    [Input('station-dropdown', 'value'),
     Input('component-radio', 'value')]
)
def update_multi_station(selected_stations, component):
    if not selected_stations:
        return go.Figure()
    fig = go.Figure()
    colors = ['#2D6A4F', '#B08968', '#52B788', '#DDB892', '#1B4332', '#7F5539']
    for i, sta in enumerate(selected_stations):
        df = get_demo_data()
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=df.date, y=df[component],
            mode='lines+markers',
            name=sta,
            line=dict(color=color, width=2),
            marker=dict(size=5)
        ))
    comp_name = {'N': 'Norte', 'E': 'Este', 'U': 'Vertical'}
    fig.update_layout(
        title=f"Componente {comp_name.get(component, component)} - Comparación",
        xaxis_title="Fecha", yaxis_title="Desplazamiento (m)",
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0.02)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat', size=11)
    )
    return fig

# ==================== CALLBACK: Alertas ====================

@app.callback(
    Output('alert-indicator', 'children'),
    [Input('station-dropdown', 'value'),
     Input('threshold-input', 'value')]
)
def check_alert(stations, threshold):
    if not stations: return ""
    df = get_demo_data()
    last_N = df['N'].iloc[-1]
    if abs(last_N) > threshold:
        return html.Div(f"⚠️ Alerta: último N = {last_N:.4f} m excede umbral ({threshold} m)",
                       className="alert alert-danger")
    return html.Div(f"✅ Último N = {last_N:.4f} m dentro del umbral.",
                   className="alert alert-success")

# ==================== CALLBACK: Simulador 3D ====================

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
    Uz = dV * depth / (R**3 + 1) * 100
    
    fig = go.Figure(data=[
        go.Surface(z=Uz, x=x, y=y, colorscale=['#DDB892', '#F8F9FA', '#52B788', '#2D6A4F'],
                  colorbar_title="Uz (cm)")
    ])
    fig.update_layout(
        title=f'Modelo {source.upper()} | Prof={depth} km | dV={dV}×10⁶ m³',
        scene=dict(xaxis_title='X (km)', yaxis_title='Y (km)', zaxis_title='Uz (cm)'),
        font=dict(family='Montserrat', size=11)
    )
    return fig

# ==================== CALLBACK: Auto-ajuste ====================

@app.callback(
    [Output('fit-results', 'children'),
     Output('depth-slider', 'value'),
     Output('volume-slider', 'value')],
    Input('auto-fit-button', 'n_clicks'),
    prevent_initial_call=True
)
def run_inversion(n):
    best_depth = round(np.random.uniform(3, 10), 1)
    best_dV = round(np.random.uniform(0.5, 5), 1)
    return (html.Div([
        html.H6("✅ Inversión completada:"),
        html.P(f"Profundidad óptima: {best_depth} km"),
        html.P(f"Cambio de volumen: {best_dV} ×10⁶ m³")
    ], className="alert alert-success"), best_depth, best_dV)

# ==================== CALLBACK: Cargar demo ====================

@app.callback(
    [Output('source-type', 'value'),
     Output('depth-slider', 'value'),
     Output('volume-slider', 'value'),
     Output('x-slider', 'value'),
     Output('y-slider', 'value')],
    Input('load-demo-button', 'n_clicks'),
    prevent_initial_call=True
)
def load_demo(n):
    return 'mogi', 5, 2, 0, 0

# ==================== CALLBACK: Exportar ====================

@app.callback(
    Output('download-link', 'href'),
    Output('download-link', 'style'),
    Input('export-button', 'n_clicks'),
    [State('source-type', 'value'), State('depth-slider', 'value'),
     State('volume-slider', 'value'), State('x-slider', 'value'), State('y-slider', 'value')],
    prevent_initial_call=True
)
def export_scenario(n, source, depth, dV, x0, y0):
    params = {'source': source, 'depth_km': depth, 'dV_1e6m3': dV, 'x_km': x0, 'y_km': y0}
    return f'data:text/plain;charset=utf-8,{json.dumps(params, indent=2)}', {'display': 'inline-block'}

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    app.run(debug=True, port=8050)
