import math

import dash
import folium
import plotly.graph_objs as go
from branca.colormap import StepColormap
from dash import Input, Output, dcc, html

from data_handler import load_areas

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
areas = load_areas()
areas_by_code = {area['code']: area for area in areas}
DEFAULT_AREA = '33100'  # Tampere Keskus
TAMPERE_CENTER = (61.4978, 23.7610)

TOTAL_POPULATION = sum(area['population'] for area in areas)


def weighted_average(key):
    """Population-weighted Tampere average for the percentage dicts."""
    categories = areas[0][key].keys()
    return {
        category: sum(a[key].get(category, 0) * a['population'] for a in areas) / TOTAL_POPULATION
        for category in categories
    }


TAMPERE_EDUCATION = weighted_average('education')
TAMPERE_ACTIVITY = weighted_average('activity')

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
FONT = dict(family='Roboto, sans-serif', size=12, color='#444342')
ACCENT = '#E8890C'
SELECTED = '#B5179E'
REFERENCE = '#9A9A9A'

DENSITY_COLORMAP = StepColormap(
    colors=['#fff5eb', '#fdd0a2', '#fd8d3c', '#d94801', '#7f2704'],
    index=[0, 50, 500, 1500, 3000, max(a['density'] for a in areas) + 1],
    vmin=0,
    vmax=max(a['density'] for a in areas) + 1,
    caption='Population density (inhabitants / km²)',
)


def base_layout(title, **extra):
    return go.Layout(
        title=title,
        plot_bgcolor='#f2f2f2',
        paper_bgcolor='#f2f2f2',
        font=FONT,
        margin=dict(l=10, r=10, t=50, b=10),
        **extra,
    )


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------
def marker_radius(population):
    # Circle AREA should grow with population, so the radius follows the square root.
    return max(3, math.sqrt(population) / 7)


def popup_html(area):
    rows = [
        ('Surface area', f"{area['surface_area_km2']:.2f} km²"),
        ('Population', f"{area['population']:,}".replace(',', ' ')),
        ('Density', f"{area['density']:,.0f} / km²".replace(',', ' ')),
        ('Average age', area['average_age']),
        ('Median income', f"{area['median_income']:,} €".replace(',', ' ')),
    ]
    body = ''.join(
        f"<tr><td style='padding-right:10px'>{label}</td><td>{value}</td></tr>" for label, value in rows
    )
    return f"<b>{area['code']} {area['name']}</b><table>{body}</table>"


def build_map(layer, selected_code):
    m = folium.Map(location=TAMPERE_CENTER, zoom_start=11)

    for area in areas:
        is_selected = area['code'] == selected_code
        if layer == 'density':
            fill = DENSITY_COLORMAP(area['density'])
            radius = 12
        else:
            fill = ACCENT
            radius = marker_radius(area['population'])

        folium.CircleMarker(
            [area['lat'], area['lon']],
            radius=radius,
            color=SELECTED if is_selected else '#555555',
            weight=3 if is_selected else 1,
            fill=True,
            fill_color=fill,
            fill_opacity=0.75 if layer == 'density' else 0.45,
            popup=folium.Popup(popup_html(area), max_width=300),
            tooltip=area['name'],
        ).add_to(m)

    if layer == 'density':
        DENSITY_COLORMAP.add_to(m)

    return m.get_root().render()


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def income_figure(selected_code):
    ordered = sorted(areas, key=lambda a: a['median_income'])
    return {
        'data': [
            go.Bar(
                x=[a['median_income'] for a in ordered],
                y=[a['name'] for a in ordered],
                customdata=[a['code'] for a in ordered],
                orientation='h',
                marker_color=[SELECTED if a['code'] == selected_code else ACCENT for a in ordered],
                hovertemplate='%{y}<br>%{x:,.0f} €<extra></extra>',
            )
        ],
        'layout': base_layout(
            'Median income by postal code area (click a bar to select)',
            xaxis={'title': 'Median income (€)'},
            yaxis={'automargin': True},
            height=900,
        ),
    }


def comparison_figure(title, area_values, tampere_values, area_name):
    categories = list(tampere_values.keys())
    return {
        'data': [
            go.Bar(
                name='Tampere (all areas)',
                y=categories,
                x=[tampere_values[c] for c in categories],
                orientation='h',
                marker_color=REFERENCE,
                hovertemplate='%{y}: %{x:.1f} %<extra>Tampere</extra>',
            ),
            go.Bar(
                name=area_name,
                y=categories,
                x=[area_values.get(c, 0) for c in categories],
                orientation='h',
                marker_color=SELECTED,
                hovertemplate='%{y}: %{x:.1f} %<extra>' + area_name + '</extra>',
            ),
        ],
        'layout': base_layout(
            f'{title}: {area_name}',
            barmode='group',
            xaxis={'title': 'Share of inhabitants (%)', 'ticksuffix': ' %'},
            yaxis={'automargin': True, 'autorange': 'reversed'},
            legend={'orientation': 'h', 'y': -0.25},
            height=380,
        ),
    }


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app = dash.Dash(__name__)
app.title = 'Tampere Data Dashboard'

app.layout = html.Div([
    html.Div(
        html.H1('Tampere Data Dashboard',
                style={'fontFamily': FONT['family'], 'color': '#444342', 'fontSize': '24px', 'margin': '5px 0'}),
        style={'backgroundColor': '#DDDDDD', 'padding': '5px 10px'},
    ),

    html.Div([
        html.Div([
            html.Label('Map layer'),
            dcc.Dropdown(
                id='layer-dropdown',
                options=[
                    {'label': 'General information (circle area = population)', 'value': 'general'},
                    {'label': 'Population density', 'value': 'density'},
                ],
                value='general',
                clearable=False,
            ),
        ], style={'flex': '1', 'minWidth': '250px'}),
        html.Div([
            html.Label('Postal code area'),
            dcc.Dropdown(
                id='area-dropdown',
                options=[{'label': f"{a['code']} {a['name']}", 'value': a['code']} for a in areas],
                value=DEFAULT_AREA,
                clearable=False,
            ),
        ], style={'flex': '1', 'minWidth': '250px'}),
    ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap', 'padding': '10px',
              'fontFamily': FONT['family']}),

    html.Iframe(id='folium-map', width='100%', height='500px', style={'border': 'none'}),

    html.Div([
        html.Div(dcc.Graph(id='education-chart'), style={'flex': '1', 'minWidth': '350px'}),
        html.Div(dcc.Graph(id='activity-chart'), style={'flex': '1', 'minWidth': '350px'}),
    ], style={'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap'}),

    dcc.Graph(id='income-bar-chart'),

    html.P('Data: Statistics Finland, Paavo – open data by postal code area, 2022.',
           style={'fontFamily': FONT['family'], 'fontSize': '12px', 'color': '#777', 'padding': '0 10px'}),
])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
@app.callback(
    Output('area-dropdown', 'value'),
    Input('income-bar-chart', 'clickData'),
    prevent_initial_call=True,
)
def select_area_from_bar(click_data):
    return click_data['points'][0]['customdata']


@app.callback(
    Output('education-chart', 'figure'),
    Output('activity-chart', 'figure'),
    Output('income-bar-chart', 'figure'),
    Input('area-dropdown', 'value'),
)
def update_charts(selected_code):
    area = areas_by_code.get(selected_code, areas_by_code[DEFAULT_AREA])
    return (
        comparison_figure('Education level', area['education'], TAMPERE_EDUCATION, area['name']),
        comparison_figure('Main activity', area['activity'], TAMPERE_ACTIVITY, area['name']),
        income_figure(area['code']),
    )


@app.callback(
    Output('folium-map', 'srcDoc'),
    Input('layer-dropdown', 'value'),
    Input('area-dropdown', 'value'),
)
def update_map(layer, selected_code):
    return build_map(layer, selected_code)


if __name__ == '__main__':
    app.run(debug=True)
