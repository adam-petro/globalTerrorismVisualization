# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from dash import Input, Output, State
import json
from scipy.sparse import data
from sklearn.cluster import DBSCAN

app = dash.Dash(__name__)

filepath = './dataset/globalterrorismdb_0221dist.csv'

px.set_mapbox_access_token(open(".mapbox_token").read())

df1 = pd.read_csv(filepath, delimiter=';', on_bad_lines='skip', low_memory=False)
df1.dataframeName = 'globalterrorismdb_0718dist.csv'
# df1.drop_duplicates(subset=['country'])
nRow, nCol = df1.shape

# print(df1.head)

def preprocess(dataset):
    dataset['latitude'] = dataset['latitude'].str.replace(',', '.')
    dataset['longitude'] = dataset['longitude'].str.replace(',', '.')
    dataset['latitude'] = pd.to_numeric(dataset['latitude'])
    dataset['longitude'] = pd.to_numeric(dataset['longitude'])
    return dataset

def binCoordinates(latitude, longitude, step_size=3):
    to_bin = lambda x: np.ceil(x / step_size) * step_size
    latbin = latitude.map(to_bin)
    lonbin = longitude.map(to_bin)
    return latbin, lonbin



def renderMap(dataset, marker_visible=False, center=None, zoom=0):
    # dataset["latbin"],dataset["lonbin"] = binCoordinates(dataset["latitude"],dataset["longitude"], step_size)
    dataset = dataset.groupby(['longitude','latitude','region_txt','country_txt']).size().to_frame(name="count").reset_index()
    dataset['size'] = 4
    # return px.density_mapbox(dataset, lat='latitude', lon='longitude', hover_name="size",
    #                  z='size', mapbox_style='light', center=center, zoom=zoom, radius=20, opacity=1)
    layer1 = go.Densitymapbox(lon=dataset['longitude'], lat=dataset['latitude'], z=dataset['count'],
                                    colorscale="Viridis")
    layer2 = go.Scattermapbox(lon=dataset['longitude'], lat=dataset['latitude'], marker=dict(size=dataset['size']))
    layers = [layer1]
    if marker_visible:
        layers.append(layer2)
    fig = go.Figure(data=layers)
    if center==None:
        center = {"lat":0, "lon":0}
    if zoom==None:
        zoom = 1
    fig.update_layout(mapbox_style="stamen-terrain",
                    mapbox_zoom=zoom, mapbox_center = center)
    return fig
 
# a = df1.groupby(['latitude','longitude','country_txt']).size().to_frame(name="count").reset_index()




# groups = a.groupby(("latbin", "lonbin",))
df1 = preprocess(df1)
fig = renderMap(df1)
print("reload")

# fig.show()



app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    ),
    html.Div(id='container', children = []),
    html.Div(id="my-output")
])

@app.callback(Output('example-graph', 'figure'),
              [Input('example-graph', 'relayoutData')],
              [State("example-graph","figure")])
def display_relayout_data(relayoutData, existingState):
    if relayoutData is not None:
        j = relayoutData
        if 'mapbox.zoom' in j:
            print(relayoutData)
            if j['mapbox.zoom']>2.5:
                fig = renderMap(df1, marker_visible=True, center = j['mapbox.center'], zoom=j['mapbox.zoom'])
                return fig
            else:
                return existingState
    return existingState
            # print(relayoutData)

if __name__ == '__main__':
    app.run_server(debug=True)

