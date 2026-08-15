import dash_bootstrap_components as dbc
from dash import html

def create_banner():
    return dbc.Navbar(
        dbc.Container([
            html.Img(src="/assets/logo_sirgas2026.png", height="60px", className="me-3"),
            html.H4("Plataforma abierta para monitoreo geodésico y simulación de deformación en la región SIRGAS",
                    className="text-light me-auto"),
            dbc.Row([
                dbc.Col(html.Div(id="kpi-stations", className="kpi-box")),
                dbc.Col(html.Div(id="kpi-last-solution", className="kpi-box")),
                dbc.Col(html.Div(id="kpi-model-date", className="kpi-box")),
            ], className="g-2")
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    )

