# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# To-do: Optimization: If existingdata and relayoutdata zoom has not changed, do not rerender everything,
# just return existing data


import dash
from dash import dcc, html
from dash.exceptions import PreventUpdate
from datetime import datetime
from matplotlib.pyplot import cla, scatter
from pandas.core.frame import DataFrame
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from dash import Input, Output, State
from dataprocessor import TerroristData

START_YEAR = 1970
END_YEAR = 2019
DEFAULT_RANGE = ['1970-01-01', '2019-12-31']
DEFAULT_RADIO_VAL = 'count'

app = dash.Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"],
                external_scripts=["https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"])
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
                                                  margin=dict(
                                                      t=0, b=10, l=0, r=0),
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
    fig = go.Figure(data=go.Pie(
        labels=dataset['weaptype1_txt'], values=dataset[DEFAULT_RADIO_VAL], customdata=dataset['eventid']),
        layout=go.Layout(
        title="Weapon type",
        autosize=True,
        # margin=dict(t=0, b=10, l=0, r=0),
        showlegend=False))
    return fig


def renderStackedAreaChart(dataset, default_groups):
    x = list(range(START_YEAR, END_YEAR+1))
    y = [0]*len(x)
    dataset = dataset.groupby(
        ['gname', 'iyear']).size().reset_index(name='nkill')

    # create dictionary {group -> list of kills per year}
    groups = dataset['gname'].unique()
    groups_dict = {}
    for group_name in groups:
        y = [0]*len(x)
        group = dataset[dataset['gname'] == group_name]
        for _, row in group.iterrows():
            y[row.iyear - START_YEAR] = row.nkill

        groups_dict[group_name] = y

    # fill chart with default groups
    # reversed order for clearer chart
    default_groups = list(reversed(default_groups))
    fig = go.Figure()
    for group_name in default_groups:
        fig.add_trace(go.Scatter(
            name=group_name,
            x=x,
            y=groups_dict[group_name],
            # hoveron='points+fills',
            # hoverinfo="name+x+y",
            stackgroup='group'
        ))
    return fig


def renderRangeSlider(dataset, val, range):
    dataset.date = pd.to_datetime(dataset.date)
    dataset = dataset.sort_values(by='date')

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(dataset['date']), y=list(dataset[val]), mode='lines'))
    fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(count=1,
                     label="YTD",
                     step="year",
                     stepmode="todate"),
                dict(count=1,
                     label="1y",
                     step="year",
                     stepmode="backward"),
                dict(count=10,
                     label="10y",
                     step="year",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
        )
    )

    print('rendering slider')
    fig.update_xaxes(range=range)
    # if 'range' not in fig.layout.xaxis:
    #     print('range not specified')
    #     fig.update_xaxes(range=DEFAULT_RANGE)
    # else:
    #     fig.update_xaxes(range=range)

    return fig


def filterDatasetByWeapon(dataset, weapon):
    dataset = dataset[dataset.weaptype1_txt == weapon]
    return dataset


def filterDatasetByDateRange(dataset, sliderState):
    if sliderState is not None and 'xaxis.range[0]' in sliderState:
        print('changed data')
        date_range = [sliderState['xaxis.range[0]'], sliderState['xaxis.range[1]']]
    else:
        date_range = DEFAULT_RANGE
    print(date_range)
    lowerBound = date_range[0].split(' ')[0].split('-')
    # lowerBound = range[0].split(' ')[0].split('-')
    lowerBound = datetime(int(lowerBound[0]), int(lowerBound[1]), int(lowerBound[2]))
    upperBound = date_range[1].split(' ')[0].split('-')
    # upperBound = range[1].split(' ')[0].split('-')
    upperBound = datetime(int(upperBound[0]), int(upperBound[1]), int(upperBound[2]))

    dataset.date = pd.to_datetime(dataset.date, format='%Y-%m-%d')
    if lowerBound == upperBound:
        dataset = dataset[dataset.date == lowerBound]
    else:
        dataset = dataset[dataset.date >= lowerBound]
        dataset = dataset[dataset.date <= upperBound]
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
df_slider = td.get_aggregated_data_by_year()

mapFig = renderMap(df_scat, df_lat_long, DEFAULT_RADIO_VAL)
pieChart = renderPieChart(td.get_weapon_data())
rangeSliderFig = renderRangeSlider(df_slider, DEFAULT_RADIO_VAL, DEFAULT_RANGE)

df_default_groups = td.get_top_groups_sorted().head(10).gname.tolist()
stackedAreaChart = renderStackedAreaChart(
    td.get_groups_data(), df_default_groups)

print("reload")

app.layout = html.Div(children=[
    html.Div(className='main-body container-fluid', children=[
        html.H1(children='Terrorist Activities Dashboard'),
        html.Div(className="upper-section row", children=[
            html.Div(className='map-with-filters col-8', children=[
                html.Div(
                    className='map-container col',
                    children=[
                        html.Div(
                            className="filter-container row",
                            children=[
                                html.Div(
                                    className='country-filter col',
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
                                    className='col',
                                    children=[
                                        html.Div(children=[
                                            dcc.Checklist(
                                                className='',
                                                id='success-checklist',
                                                options=[
                                                    {'label': 'Successful attacks',
                                                     'value': 1},
                                                    {'label': 'Unsuccessful attacks',
                                                     'value': 0},
                                                ],
                                                value=[1, 0]
                                            )]),
                                        dcc.RadioItems(
                                            className='radio-items',
                                            id='deaths-radio',
                                            options=[
                                                {'label': 'Deaths',
                                                    'value': 'nkill'},
                                                {'label': 'No. of attacks',
                                                 'value': 'count'}
                                            ],
                                            value=DEFAULT_RADIO_VAL
                                        )
                                    ])

                            ],
                        ),
                        html.Div(className='row', children=[
                            dcc.Graph(
                                id='main-map',
                                figure=mapFig
                            )]),
                    dcc.Graph(
                        id="date-slider",
                        figure=rangeSliderFig
                    ),
                    ]
                ),
            ]),
            html.Div(className='additional-chart col-4',
                     children=[
                        dcc.Graph(id='pie-chart',
                                    figure=go.Figure(pieChart)),
                        html.Div(className="alert alert-secondary", children=[
                            html.Div(className="row", children=[
                                html.Div(className="col d-flex flex-column justify-content-between", children=[
                                     html.P(children=["Map is displaying data for the following weapon type: "]),
                                     html.P(id="weapon-type-text",
                                               children=["all weapons"]),
                                     html.Button(
                                         "Reset Selection", className="btn btn-primary w-75", id="reset-pieChart-weapons-button")
                                 ]),
                                html.Div(className="col d-flex flex-column justify-content-between", children=[
                                     html.P(id="selected-points-text", children=[]),
                                     html.Button(
                                         "Reset Selection", className="btn btn-primary w-75", id="reset-pieChart-selectetData-button")
                                 ])
                             ]),
                         ])
                     ]),
            # html.Div(className='additional-chart',
            #          children=[dcc.Graph(id='stacked-area-chart', figure=go.Figure(stackedAreaChart))])
        ])
    ])

])
@app.callback(Output('selected-points-text', 'children'),
              Input('main-map', 'selectedData'),
              State('main-map', 'selectedData'))
def updateTextWithSelectedPoints(_, mainMapSelectedData):
    text="Pie Chart is displaying data for all the points visible on the map"
    if mainMapSelectedData != None and mainMapSelectedData['points'] != None and len(mainMapSelectedData['points']) != 0:
        text=f"Displaying data for {len(mainMapSelectedData['points'])} selected points on the map"
    return text



@app.callback(Output('weapon-type-text', 'children'),
              Input('pie-chart', 'clickData'),
              State('pie-chart', 'clickData'))
def updateTextWithSelectedWeapon(_, pieChartClickData):
    weapon="All weapons"
    if pieChartClickData != None:
        weapon=pieChartClickData["points"][0]['label']
    return weapon


@app.callback(Output('pie-chart', 'clickData'),
              Input('reset-pieChart-weapons-button', 'n_clicks'))
def resetPieChartClickData(_):
    return None


@ app.callback(Output('pie-chart', 'figure'),
              Input('main-map', 'selectedData'),
              Input('main-map', 'relayoutData'),
              Input('date-slider', 'relayoutData'),
              Input('reset-pieChart-weapons-button', 'n_clicks'),
              Input('success-checklist', 'value'),
              Input('deaths-radio', 'value'),
              Input('country-dropdown', 'value'),
              State('main-map', 'selectedData'),
              State('date-slider', 'relayoutData'),
              State('success-checklist', 'value'),
              State('country-dropdown', 'value')
              )
def updatePieChartAccordingly(_, __, ___, ____, _____, ______, _______, selectedData, sliderState, successState, countries):
    if selectedData is not None and 'points' in selectedData:
        ids=[]
        for point in selectedData['points']:
            ids.append(str(point['customdata'][0]))
        dataset=td.get_weapon_data(ids)
    else:
        dataset=td.get_weapon_data()
    # else:
    #     dataset = td.get_weapon_data()
    # Filter by selected countries
    if countries is not None and len(countries) > 0:
        dataset=dataset[dataset.country_txt.isin(countries)]
    # Filter by selected time window
    #extract range state 
    dataset=filterDatasetByDateRange(dataset, sliderState)
    # Filter by successful/unsuccessful
    dataset=filterDatasetBySuccess(dataset, success=successState)
    return renderPieChart(dataset)

@app.callback(Output('main-map', 'selectedData'),
              Input('reset-pieChart-selectetData-button', 'n_clicks'))
def resetMapSelectedData(_):
    return None

@app.callback(Output('date-slider', 'figure'),
              Input('deaths-radio', 'value'),
              State('deaths-radio', 'value'),
              State('date-slider', 'relayoutData')
              )
def updateSliderAccordingly(_, deathsState, sliderState):
    # Extract current date range
    if sliderState is not None and 'xaxis.range[0]' in sliderState:
        print(sliderState)
        range = [sliderState['xaxis.range[0]'].split(' ')[0], sliderState['xaxis.range[1]'].split(' ')[0]]
    else:
        range = DEFAULT_RANGE
    # Rerender slider based on radio selector value
    fig = renderRangeSlider(df_slider, deathsState, range)
    return fig

@ app.callback(Output('main-map', 'figure'),
              Input('main-map', 'relayoutData'),
              Input('date-slider', 'relayoutData'),
              Input('country-dropdown', 'value'),
              Input('success-checklist', 'value'),
              Input('deaths-radio', 'value'),
              Input('pie-chart', 'clickData'),
              Input('reset-pieChart-weapons-button', 'n_clicks'),
              State("main-map", "figure"),
              State('success-checklist', 'value'),
              State('deaths-radio', 'value'),
              State('pie-chart', 'clickData'),
              State('date-slider', 'relayoutData'),
              State('country-dropdown', 'value')
              )
def updateMapAccordingly(_, __, ___, ____, _____, ______, _______,
                         mapFigure, successState, deathsState, pieChartState, sliderState, countries):
    # Filter by year
    df_lat_long_fil=filterDatasetByDateRange(df_lat_long, sliderState)
    df_scat_fil=filterDatasetByDateRange(df_scat, sliderState)
    # Filter by weapon selected
    if pieChartState is not None:
        weapon=pieChartState["points"][0]['label']
        df_lat_long_fil=filterDatasetByWeapon(df_lat_long, weapon)
        df_scat_fil=filterDatasetByWeapon(df_scat_fil, weapon)
    # Filter by successful/unsuccessful
    df_lat_long_fil=filterDatasetBySuccess(
        df_lat_long_fil, success=successState)
    df_scat_fil=filterDatasetBySuccess(df_scat_fil, success=successState)
    # Filter by countries
    if countries is not None and len(countries) > 0:
        df_scat_fil=df_scat_fil[df_scat_fil.country_txt.isin(countries)]
        df_lat_long_fil=df_lat_long_fil[df_lat_long_fil.country_txt.isin(
            countries)]
    # Update the map with the existing or new data
    zoom=mapFigure['layout']['mapbox']['zoom']
    center=mapFigure['layout']['mapbox']['center']
    if zoom > 2.5:
        fig=renderMap(df_scat_fil, df_lat_long_fil, deathsState,
                        marker_visible=True, center=center, zoom=zoom)
        return fig
    else:
        return renderMap(df_scat_fil, df_lat_long_fil, deathsState, center=center, zoom=zoom)


if __name__ == '__main__':
    app.run_server(debug=True)
