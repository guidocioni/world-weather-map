import json
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import pandas as pd
import numpy as np
from dash_extensions.javascript import Namespace
from dash import Dash
from dash.dependencies import Input, Output
import os

apiURL = "https://api.mapbox.com/directions/v5/mapbox"
apiKey = os.environ['MAPBOX_KEY']

mapURL = 'https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}{r}?access_token=' + apiKey
attribution = '© <a href="https://www.mapbox.com/feedback/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'

# cache this
def read_data():
    df = pd.read_pickle("output.pkl").reset_index()
    df = df.rename(columns={'heightOfStationGroundAboveMeanSeaLevel':'alt',
        'longitude':'lon', 'latitude':'lat', 'stationOrSiteName':'station'})

    df = df.drop_duplicates(subset=['station'])

    return df


with open("custom.geo.json", 'r') as f:
    statesData = json.load(f)


def get_data(color_prop):
    df = read_data().dropna(subset=[color_prop])
    # drop irrelevant columns
    df = df[['lat', 'lon', 'alt', 'station', 'date', color_prop]]
    dicts = df.to_dict('rows')
    for item in dicts:
        item["tooltip"] = "Measured at %s : %2.1f" % (item["date"], item[color_prop])
        item["popup"] = "%s, altitude %4.0f" %  (item["station"], item["alt"])
    geojson = dlx.dicts_to_geojson(dicts, lon="lon", lat="lat")
    geobuf = dlx.geojson_to_geobuf(geojson)  # convert to geobuf

    return geobuf


def get_minmax(variable):
    df = read_data().dropna(subset=[variable])
    df_variable = df[variable]  # pick one variable
    return dict(min=df_variable.values.min(), max=df_variable.values.max())


# Setup a few color scales.
csc_map = {"Rainbow": ['purple', 'blue', 'green', 'yellow', 'red'], 
           "Hot": ['yellow', 'red', 'black'],
           "Viridis": "Viridis"}
csc_options = [dict(label=key, value=json.dumps(csc_map[key]))
               for key in csc_map]
default_csc = "Rainbow"
dd_csc = dcc.Dropdown(options=csc_options, value=json.dumps(
    csc_map[default_csc]), id="dd_csc", clearable=False)
# Setup state options.

default_variable = "airTemperature"
variable_options = [
{'label': 'Temperature', 'value': 'airTemperature'},
{'label': 'Total Precipitaton', 'value': 'totalPrecipitationOrTotalWaterEquivalent'},
{'label': 'Snow depth', 'value': 'totalSnowDepth'},
{'label': 'Dewpoint', 'value': 'dewpointTemperature'},
{'label': 'RH', 'value': 'relativeHumidity'},
{'label': 'Maximum gust', 'value': 'maximumWindGustSpeed'},
{'label': 'Total Precipitation (24hrs)', 'value': 'totalPrecipitationPast24Hours'},
{'label': 'Radiation', 'value': 'globalSolarRadiationIntegratedOverPeriodSpecified'},
{'label': 'Sunshine duration', 'value': 'totalSunshine'},
]
dd_variable = dcc.Dropdown(options=variable_options,
                        value=default_variable, id="dd_variable", clearable=False)

ns = Namespace("dlx", "scatter")
geojson_countries = dl.GeoJSON(data=statesData, id="geojson_countries",
     options=dict(style=dict(weight=1, opacity=0.7, color='white', fillOpacity=0)))

# Create the app.
chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
app = Dash(external_scripts=[chroma], prevent_initial_callbacks=True)
server = app.server

def serve_layout():
    minmax = get_minmax(default_variable)

    # Create a colorbar.
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
                     superClusterOptions=dict(radius=20),  # adjust cluster size
                     hideout=dict(colorscale=csc_map[default_csc], colorProp=default_variable, **minmax))


    layout = html.Div([
        dl.Map([
            dl.LayersControl(
            [
            dl.BaseLayer(dl.TileLayer(url=mapURL, attribution=attribution, tileSize=512, zoomOffset=-1), name='map', checked=True),
            dl.Overlay(dl.WMSTileLayer(url="https://maps.dwd.de/geoserver/ows?",
                                            layers="dwd:SAT_WELT_KOMPOSIT", 
                                            format="image/png", 
                                            transparent=True, opacity=0.7,
                                            version='1.3.0',
                                            detectRetina=True), name='sat world', checked=True),
            dl.Overlay(dl.WMSTileLayer(url="https://maps.dwd.de/geoserver/ows?",
                                            layers="dwd:SAT_EU_RGB", 
                                            format="image/png", 
                                            transparent=True, opacity=0.7,
                                            version='1.3.0',
                                            detectRetina=True), name='sat eu', checked=True),
            dl.Overlay(dl.WMSTileLayer(url="https://maps.dwd.de/geoserver/ows?",
                                                    layers="dwd:WN-Produkt", 
                                                    format="image/png", 
                                                    transparent=True, opacity=0.7,
                                                    version='1.3.0',
                                                    detectRetina=True), name='radar DE', checked=True),
            dl.Overlay([geojson, colorbar], name='obs DE', checked=True)
            ]),
            geojson_countries,
            ]),
        html.Div([dd_variable, dd_csc],
            style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"})
    ], style={'width': '100%', 'height': '90vh', 'margin': "auto", "display": "block", "position": "relative"})

    return layout

app.layout = serve_layout

@app.callback([Output("geojson", "hideout"), Output("geojson", "data"), Output("colorbar", "colorscale"),
               Output("colorbar", "min"), Output("colorbar", "max"), Output("geojson", "colorProp")],
              [Input("dd_csc", "value"), Input("dd_variable", "value")])
def update(csc, variable):
    csc, data, mm = json.loads(csc), get_data(variable), get_minmax(variable)
    hideout = dict(colorscale=csc, colorProp=variable, **mm)
    return hideout, data, csc, mm["min"], mm["max"], variable


if __name__ == '__main__':
    app.run_server()
