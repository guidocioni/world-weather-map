import json
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
from dash_extensions.javascript import Namespace
from dash import Dash
from dash.dependencies import Input, Output, State
import os
from mnw_api import MNWApi
from flask_caching import Cache

mnw = MNWApi()

apiURL = "https://api.mapbox.com/directions/v5/mapbox"
apiKey = os.environ['MAPBOX_KEY']

mapURL = 'https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}{r}?access_token=' + apiKey
attribution = '© <a href="https://www.mapbox.com/feedback/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'



with open("provinces_it.geojson", 'r') as f:
    statesData = json.load(f)


# Setup a few color scales.
csc_map = {"Rainbow": ['purple', 'blue', 'green', 'yellow', 'red'], 
           "Hot": ['yellow', 'red', 'black'],
           "Viridis": "Viridis"}
csc_options = [dict(label=key, value=json.dumps(csc_map[key]))
               for key in csc_map]
default_csc = "Rainbow"
dd_csc = dcc.Dropdown(options=csc_options, value=json.dumps(
    csc_map[default_csc]), id="dd_csc", clearable=False)

default_variable = "temperature"
variable_options = [
{'label': 'temperature', 'value': 'temperature'},
{'label': 'pressure', 'value': 'smlp'},
{'label': 'humidity', 'value': 'rh'},
{'label': 'wind_speed', 'value': 'wind_speed'},
{'label': 'wind_gust', 'value': 'wind_gust'},
{'label': 'rain_rate', 'value': 'rain_rate'},
{'label': 'daily_rain', 'value': 'daily_rain'},
{'label': 'dew_point', 'value': 'dew_point'},
{'label': 'rad', 'value': 'rad'},
]


ns = Namespace("dlx", "scatter")
geojson_countries = dl.GeoJSON(data=statesData, id="geojson_countries",
     options=dict(style=dict(weight=1, opacity=0.7, color='white', fillOpacity=0)))

# Create the app.
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
app = Dash(external_scripts=[chroma], prevent_initial_callbacks=True, url_base_pathname='/weathermap/')
server = app.server

cache = Cache(server, config={'CACHE_TYPE': 'filesystem', 
                              'CACHE_DIR': '/tmp'})


@cache.memoize(900)
def get_df():
    df = mnw.get_realtime_stations(country='IT')

    return df


@cache.memoize(900)
def get_data(variable):
    df = get_df().dropna(subset=[variable])
    # drop irrelevant columns
    df = df[['latitude', 'longitude', 'altitude', 'name', 'observation_time_local', variable]]
    dicts = df.to_dict('rows')
    for item in dicts:
        item["tooltip"] = "Measured at %s : %2.1f" % (item["observation_time_local"], item[variable])
        item["popup"] = "%s, altitude: %4.0f m" %  (item["name"], item["altitude"])
    geojson = dlx.dicts_to_geojson(dicts, lon="longitude", lat="latitude")
    geobuf = dlx.geojson_to_geobuf(geojson)

    return geobuf


@cache.memoize(900)
def get_minmax(variable):
    df = get_df().dropna(subset=[variable])
    df_variable = df[variable] 

    return dict(min=df_variable.values.min(), max=df_variable.values.max())


def serve_layout():
    dd_variable = dcc.Dropdown(options=variable_options,
                           value=default_variable, id="dd_variable", clearable=False)
    minmax = get_minmax(default_variable)
    # # Create a colorbar.
    colorbar = dl.Colorbar(
    colorscale=csc_map[default_csc], id="colorbar", width=20, height=150, **minmax)

    geojson = dl.GeoJSON(data=get_data(default_variable), id="geojson", format="geobuf",
                     zoomToBounds=True,  # when true, zooms to bounds when data changes
                     cluster=True,  # when true, data are clustered
                     # how to draw clusters
                     clusterToLayer=ns("clusterToLayer"),
                     # when true, zooms to bounds of feature (e.g. cluster) on click
                     zoomToBoundsOnClick=True,
                     # how to draw points
                     options=dict(pointToLayer=ns("pointToLayer")),
                     superClusterOptions=dict(radius=0.1),  # adjust cluster size
                     hideout=dict(colorscale=csc_map[default_csc], colorProp=default_variable, **minmax))

    times = pd.date_range(start=pd.to_datetime('now', utc=True).round('15min') - pd.Timedelta('2hours'),
              end=pd.to_datetime('now', utc=True).round('15min') - pd.Timedelta('15min'),
              freq='5min')
    latest = times[-1].strftime('%Y-%m-%dT%H:%M:00.000Z')

    numdate= [x for x in range(len(times))]
    marks = {numd:date.strftime('%H:%M') for numd, date in zip(numdate, times)}

    slider = dcc.Slider(id='time_slider', min=numdate[0],
                                          max=numdate[-1],
                                          value=numdate[-1],
                                          marks=marks)


    layout = html.Div([
        dl.Map([
            dl.LayersControl(
            [
            dl.BaseLayer(dl.TileLayer(url=mapURL, attribution=attribution,
                                      tileSize=512, zoomOffset=-1), name='map', checked=True),
            dl.Overlay(dl.WMSTileLayer(url="https://maps.dwd.de/geoserver/ows?",
                                            layers="dwd:SAT_EU_RGB", 
                                            format="image/png", 
                                            transparent=True, opacity=0.7,
                                            version='1.3.0',
                                            detectRetina=True), name='sat eu', checked=True),
            dl.Overlay(dl.WMSTileLayer(id='radar_it',
                                       url="http://www.protezionecivile.gov.it/geowebcache/service/wms?&time=%s" % latest,
                                       layers="radar:sri",
                                       transparent=True,
                                       format="image/png",
                                       opacity=0.9,
                                       version='1.1.1'),
            name='radar IT', checked=True),
            dl.Overlay([geojson, colorbar], name='obs', checked=True)
            ]),
            geojson_countries,
            ], center=[41, 12], zoom=6),
        html.Div(id='date-div', style={'display': 'none'}, children=[times.strftime('%Y-%m-%dT%H:%M:00.000Z')]),
        html.Div([slider],
            style={"position": "absolute", "bottom": "20px",
            "left": "10px", "z-index": "1000", "width": "800px",
            "background-color":'rgba(1, 1, 1, 0.3)'}),
        html.Div([dd_variable],
            style={"position": "absolute", "top": "250px", "right": "16px", "z-index": "1000", "width": "100px"})
    ], style={'width': '100%', 'height': '90vh', 'margin': "auto", "display": "block", "position": "relative"})

    return layout

app.layout = serve_layout


@app.callback([Output("geojson", "hideout"), Output("geojson", "data"),
               Output("colorbar", "min"), Output("colorbar", "max"), Output("geojson", "colorProp")],
              [Input("dd_variable", "value")])
def update(variable):
    print('triggered update')
    data, mm = get_data(variable), get_minmax(variable)
    hideout = dict(colorProp=variable, **mm)

    return hideout, data, mm["min"], mm["max"], variable


@app.callback([Output("radar_it", "url")],
              [Input("time_slider", "value")],
              [State("date-div", "children")])
def update_time(time, dates):
    url = "http://www.protezionecivile.gov.it/geowebcache/service/wms?&time=%s" % dates[0][time]

    return [url]



if __name__ == '__main__':
    app.run_server()
