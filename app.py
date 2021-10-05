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
from dataprocessor import TerroristData

app = dash.Dash(__name__)
server = app.server

filepath = './dataset/globalterrorismdb_0221dist.csv'
mapbox_access_token = (open(".mapbox_token").read())

# print(df1.head)
td = TerroristData()


def renderMap(s_dataset, d_dataset, marker_visible=False, center=None, zoom=0):
    density_dataset = d_dataset.groupby(['longitude','latitude']).size().to_frame(name="count").reset_index()
    layer1 = go.Densitymapbox(lon=density_dataset['longitude'], lat=density_dataset['latitude'], z=density_dataset['count'],
                                    colorscale="Viridis")
    layers = [layer1]

    if marker_visible:
        scatter_dataset = s_dataset.groupby(['longitude','latitude','attacktype1_txt','iyear','imonth','iday']).size().to_frame(name="count").reset_index()
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


df_lat_long = td.get_lat_long()
df_scat = td.get_data_for_scat()

df_country = td.get_country()
df_year = td.get_years()

fig = renderMap(df_scat, df_lat_long)

print("reload")

app.layout = html.Div(children=[
    html.H1(children='Terrorist Activities Dashboard'),
        html.Div(
            className="div-for-dropdown",
            children=[
                # Dropdown to select times
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[
                        {
                            'label': i.country_txt,
                            'value': i.country_txt
                        }
                        for index, i in df_country.iterrows()
                    ],
                    multi=True,
                    placeholder="Filter by country...",
                )

            ],
        ),
    dcc.Graph(
        id='main-map',
        figure=fig
    ),
    dcc.Slider(
            id='year-slider',
            min=df_year['iyear'].min(),
            max=df_year['iyear'].max(),
            value=df_year['iyear'].max(),
            marks={str(year): str(year) for year in df_year['iyear'].unique()},
            step=5
        )

])


@app.callback(Output('main-map', 'figure'),
                Input('main-map', 'relayoutData'),
                Input('year-slider', 'value'),
                Input('country-dropdown', 'value'),
                State("main-map", "figure"),
              )
def display_relayout_data(relayoutData, selected_year, countries, existingState):
    ctx = dash.callback_context
    print(countries)
    if not ctx.triggered:
        call_bk_item = None
    else:
        call_bk_item = ctx.triggered[0]['prop_id'].split('.')[0]

    df_scat_fil = df_scat[df_scat.iyear <= selected_year]
    df_lat_long_fil = df_lat_long[df_lat_long.iyear <= selected_year]

    if countries is not None and len(countries)>0:
        df_scat_fil = df_scat_fil[df_scat_fil.country_txt.isin(countries)]
        df_lat_long_fil = df_lat_long_fil[df_lat_long_fil.country_txt.isin(countries)]

    if relayoutData is not None and call_bk_item is not None:
        j = relayoutData
        if 'mapbox.zoom' in j:
            if j['mapbox.zoom']>2.5:
                fig = renderMap(df_scat_fil, df_lat_long_fil, marker_visible=True, center = j['mapbox.center'], zoom=j['mapbox.zoom'])
                return fig
            else:
                return renderMap(df_scat_fil, df_lat_long_fil, center = j['mapbox.center'], zoom=j['mapbox.zoom'])
        else:
            return renderMap(df_scat_fil, df_lat_long_fil)

    return existingState


if __name__ == '__main__':
    app.run_server()

