# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# To-do: Optimization: If existingdata and relayoutdata zoom has not changed, do not rerender everything,
# just return existing data


import dash
from dash import dcc, html
from dash.exceptions import PreventUpdate
from matplotlib.pyplot import cla, scatter
from pandas.core.frame import DataFrame
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


def renderMap(s_dataset, d_dataset, criterium, marker_visible=False, center=None, zoom=1):
    if not marker_visible:
        if criterium == 'count':
            density_dataset = d_dataset.groupby(
                ['longitude', 'latitude']).size().to_frame(name="count").reset_index()
        elif criterium == 'nkill':
            density_dataset = d_dataset.groupby(
                ['longitude', 'latitude']).nkill.sum().reset_index()
        layer1 = go.Densitymapbox(lon=density_dataset['longitude'], lat=density_dataset['latitude'], z=density_dataset[criterium],
                                colorscale="Viridis", radius=15)
        layers = [layer1]

    elif marker_visible:
        marker = dict(
            opacity=0.3,
            allowoverlap=True,
            color="red",
        )
        customdata = np.stack((s_dataset['eventid'].array, s_dataset['attacktype1_txt'].array, s_dataset['iday'].array,
                               s_dataset['imonth'].array, s_dataset['iyear'].array), axis=-1)
        layer2 = go.Scattermapbox(lon=s_dataset['longitude'], lat=s_dataset['latitude'], marker=marker,
                                  customdata=customdata, hovertemplate="<b>%{customdata[4]}-%{customdata[3]}-%{customdata[2]}</b><br><br>%{customdata[1]}")
        layers = [layer2]

    fig = go.Figure(data=layers, layout=go.Layout(autosize=True,
                                                  showlegend=False,
                                                  mapbox=dict(
                                                      accesstoken=mapbox_access_token,
                                                      style="basic",
                                                  ),))
    if center == None:
        center = {"lat": 0, "lon": 0}
    if zoom == None:
        zoom = 1
    fig.update_layout(mapbox_zoom=zoom, mapbox_center=center)
    return fig

def renderPieChart(dataset):
    fig = go.Figure(data=go.Pie(labels=dataset['weaptype1_txt'], values=dataset['count']))
    return fig



def filterDatasetByDateRange(dataset, range):
    lowerBound = range[0]
    upperBound = range[1]
    if lowerBound == upperBound:
        dataset = dataset[dataset.iyear == lowerBound]
    else:
        dataset = dataset[dataset.iyear >= lowerBound]
        dataset = dataset[dataset.iyear <= upperBound]
    return dataset


def filterDatasetBySuccess(dataset, success):
    if 1 in success and 0 in success:
        return dataset
    elif 1 in success and 0 not in success:
        return dataset[dataset.success == 1]
    elif 1 not in success and 0 in success:
        return dataset[dataset.success == 0]
    else:
        return dataset[dataset.success == -1]


df_lat_long = td.get_lat_long()
df_scat = td.get_data_for_scat()

df_country = td.get_country()

mapFig = renderMap(df_scat, df_lat_long, 'count')
pieChart = renderPieChart(td.get_weapon_data())

print("reload")

app.layout = html.Div(children=[
    html.H1(children='Terrorist Activities Dashboard'),
    html.Div(className='main-body', children=[
        html.Div(className='map-with-filters', children=[
            html.Div(
                className='map-container',
                children=[
                    html.Div(
                        className="filter-container flex-row",
                        children=[
                            html.Div(
                                className='country-filter',
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
                                    ), ]),
                            html.Div(
                                className='additional-filters',
                                children=[
                                    dcc.Checklist(
                                        className='checklist',
                                        id='success-checklist',
                                        options=[
                                            {'label': 'Successful attacks',
                                                'value': 1},
                                            {'label': 'Unsuccessful attacks',
                                                'value': 0},
                                        ],
                                        value=[1, 0]
                                    ),
                                    dcc.RadioItems(
                                        className='radio-items',
                                        id='deaths-radio',
                                        options=[
                                            {'label': 'Deaths', 'value': 'nkill'},
                                            {'label': 'No. of attacks',
                                                'value': 'count'}
                                        ],
                                        value='count'
                                    )
                                ])

                        ],
                    ),
                    dcc.Graph(
                        id='main-map',
                        figure=mapFig
                    ),
                    dcc.RangeSlider(id="year-slider",
                                    min=1970,
                                    max=2019,
                                    dots=True,
                                    value=[2010, 2012],
                                    marks={
                                        '1970': '1970',
                                        '1980': '1980',
                                        '1990': '1990',
                                        '2000': '2000',
                                        '2010': '2010',
                                        '2019': '2019'
                                    },
                                    tooltip={
                                        'always_visible': True
                                    }
                                    ),
                ]
            ),
        ]),
        html.Div(className='additional-charts',

                 children=[dcc.Graph(id='pie-chart',figure=go.Figure(pieChart))])
    ])

])
@app.callback(Output('pie-chart', 'figure'),
              Input('main-map', 'selectedData'))
def updatePieChartAccordingly(selectedData):
    if selectedData==None:
        raise PreventUpdate
    if 'points' in selectedData:
        ids = []
        for point in selectedData['points']:
            ids.append(str(point['customdata'][0]))
        return renderPieChart(td.get_weapon_data(ids))


@app.callback(Output('main-map', 'figure'),
              Input('main-map', 'relayoutData'),
              Input('year-slider', 'value'),
              Input('country-dropdown', 'value'),
              Input('success-checklist', 'value'),
              Input('deaths-radio', 'value'),
              State("main-map", "figure"),
              State('success-checklist', 'value'),
              State('deaths-radio', 'value'),
              )
def updateMapAccordingly(relayoutData, year_range, countries, successFilter, deathsFilter, mapState, successState, deathsState):
    ctx = dash.callback_context
    if not ctx.triggered:
        call_bk_item = None
    else:
        call_bk_item = ctx.triggered[0]['prop_id'].split('.')[0]

    df_lat_long_fil = filterDatasetByDateRange(df_lat_long, year_range)
    df_scat_fil = filterDatasetByDateRange(df_scat, year_range)

    df_lat_long_fil = filterDatasetBySuccess(
        df_lat_long_fil, success=successState)
    df_scat_fil = filterDatasetBySuccess(df_scat_fil, success=successState)

    if countries is not None and len(countries) > 0:
        df_scat_fil = df_scat_fil[df_scat_fil.country_txt.isin(countries)]
        df_lat_long_fil = df_lat_long_fil[df_lat_long_fil.country_txt.isin(
            countries)]

    if relayoutData is not None and call_bk_item is not None:
        j = relayoutData
        if 'mapbox.center' not in j:
            center = mapState['layout']['mapbox']['center']
        else:
            center = j['mapbox.center']
        if 'mapbox.zoom' in j:
            if j['mapbox.zoom'] > 2.5:
                fig = renderMap(df_scat_fil, df_lat_long_fil, deathsState,
                                marker_visible=True, center=center, zoom=j['mapbox.zoom'])
                return fig
            else:
                return renderMap(df_scat_fil, df_lat_long_fil, deathsState, center=center, zoom=j['mapbox.zoom'])
        else:
            return mapState

    return mapState


if __name__ == '__main__':
    app.run_server(debug=True)
