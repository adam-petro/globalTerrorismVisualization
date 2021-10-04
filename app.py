# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

## To-do: Optimization: If existingdata and relayoutdata zoom has not changed, do not rerender everything,
## just return existing data


import dash
from dash import dcc, html
from matplotlib.pyplot import scatter
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from dash import Input, Output, State


app = dash.Dash(__name__)
server = app.server

filepath = './dataset/globalterrorismdb_0221dist.csv'
mapbox_access_token = "pk.eyJ1IjoicmFraGVlc2hhaCIsImEiOiJja3VjZTFld3UwYjc2Mm5ydmVnZjV4dXRqIn0.kk4UeC1uj6aE8Wq4JbS_Mw"#(open(".mapbox_token").read())

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



def renderMap(dataset, marker_visible=False, center=None, zoom=0):
    density_dataset = dataset.groupby(['longitude','latitude']).size().to_frame(name="count").reset_index()
    layer1 = go.Densitymapbox(lon=density_dataset['longitude'], lat=density_dataset['latitude'], z=density_dataset['count'],
                                    colorscale="Viridis")
    layers = [layer1]

    if marker_visible:
        scatter_dataset = dataset.groupby(['longitude','latitude','attacktype1_txt','iyear','imonth','iday']).size().to_frame(name="count").reset_index()
        marker = dict(
            opacity=0.3,
            allowoverlap=True,
            color="red",
        )
        customdata = np.stack((scatter_dataset['attacktype1_txt'].array,scatter_dataset['iday'].array,scatter_dataset['imonth'].array,scatter_dataset['iyear'].array), axis=-1)
        layer2 = go.Scattermapbox(lon=scatter_dataset['longitude'], lat=scatter_dataset['latitude'], marker=marker,  customdata=customdata, hovertemplate = "<b>%{customdata[3]}-%{customdata[2]}-%{customdata[1]}</b><br><br>%{customdata[0]}")
        layers.append(layer2)

    fig = go.Figure(data=layers, layout=go.Layout(autosize=True,
            showlegend=False,
            mapbox=dict(
                accesstoken=mapbox_access_token,
                style="basic",
            ),))
    if center==None:
        center = {"lat":0, "lon":0}
    if zoom==None:
        zoom = 1
    fig.update_layout(mapbox_zoom=zoom, mapbox_center = center)
    return fig
 




df1 = preprocess(df1)
fig = renderMap(df1)
print("reload")




app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='main-map',
        figure=fig
    ),
])

@app.callback(Output('main-map', 'figure'),
              [Input('main-map', 'relayoutData')],
              [State("main-map","figure")])
def display_relayout_data(relayoutData, existingState):
    if relayoutData is not None:
        j = relayoutData
        if 'mapbox.zoom' in j:
            if j['mapbox.zoom']>2.5:
                fig = renderMap(df1, marker_visible=True, center = j['mapbox.center'], zoom=j['mapbox.zoom'])
                return fig
            else:
                return renderMap(df1, center = j['mapbox.center'], zoom=j['mapbox.zoom'])
    return existingState

if __name__ == '__main__':
    app.run_server()

