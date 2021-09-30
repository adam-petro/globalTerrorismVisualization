# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from dash import Input, Output
import json

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

def reRenderMap(dataset, step_size=3,):
    dataset["latbin"],dataset["lonbin"] = binCoordinates(dataset["latitude"],dataset["longitude"], step_size)
    dataset = dataset.groupby(['latbin','lonbin','region_txt','country_txt']).size().to_frame(name="count").reset_index()
    dataset['size'] = np.maximum(dataset['count'],5)
    dataset['size'] = np.minimum(dataset['size'],7000)
    fig = go.Figure(go.Scattermapbox(lat=dataset['latbin'], lon=dataset['lonbin'],mode='markers', hoverinfo='lat+lon', marker=dict(size=dataset['size'],showscale=True)))
    fig.update_layout(mapbox_style='open-street-map')
    return fig 

def renderMap(dataset, step_size=3, center=None, zoom=0):
    dataset["latbin"],dataset["lonbin"] = binCoordinates(dataset["latitude"],dataset["longitude"], step_size)
    dataset = dataset.groupby(['latbin','lonbin','region_txt','country_txt']).size().to_frame(name="count").reset_index()
    dataset['size'] = np.maximum(dataset['count'],5)
    dataset['size'] = np.minimum(dataset['size'],7000)
    return px.scatter_mapbox(dataset, lat='latbin', lon='lonbin', hover_name="size",
                     color="region_txt", size='size', size_max=50, mapbox_style='open-street-map', center=center, zoom=zoom)

# a = df1.groupby(['latitude','longitude','country_txt']).size().to_frame(name="count").reset_index()




# groups = a.groupby(("latbin", "lonbin",))
df1 = preprocess(df1)
fig = renderMap(df1, step_size=0.5)
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
              [Input('example-graph', 'relayoutData')])
def display_relayout_data(relayoutData):
    if relayoutData is not None:
        j = relayoutData
        if 'mapbox.zoom' in j:
            print(relayoutData)
            if j['mapbox.zoom']!=0:
                fig = renderMap(df1, 10/(j['mapbox.zoom']), j['mapbox.center'], j['mapbox.zoom'])
                return fig
            else:
                fig = renderMap(df1, center=j['mapbox.center'], zoom=j['mapbox.zoom'])
                return fig
    fig = renderMap(df1, center=j['mapbox.center'], zoom=j['mapbox.zoom'])
    return fig
            # print(relayoutData)

if __name__ == '__main__':
    app.run_server(debug=True)
