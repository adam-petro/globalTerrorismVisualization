# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# To-do: Optimization: If existingdata and relayoutdata zoom has not changed, do not rerender everything,
# just return existing data


import dash
from dash import dcc, html
from dash.exceptions import PreventUpdate
from datetime import datetime
from matplotlib.pyplot import cla, scatter
from numpy.lib.index_tricks import s_
from pandas.core.frame import DataFrame
import plotly.express as px
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from dash import Input, Output, State
from dataprocessor import TerroristData

START_YEAR = 1970
END_YEAR = 2019
DEFAULT_RANGE = ['2010-01-01', '2019-12-31']
DEFAULT_RADIO_VAL = 'count'
HIGHLIGHTED_ATTACKS = pd.read_json(
    './highlighted_attacks.json', dtype={'date': 'datetime', 'summary': str, 'source': str})
HIGHLIGHTED_ATTACKS['date'] = HIGHLIGHTED_ATTACKS['date'].dt.strftime(
    '%Y-%-m')  # format the object
SELECTED_ATTACK_TYPE_COLUMN = None
SELECTED_WEAPON_TYPE_COLUMN = None
# DEFAULT_COLOR = '#ffa600'
# SELECTION_COLOR = '#bc5090'
# HIGHLIGHT_COLOR = '#003f5c'
DEFAULT_COLOR = '#1b9e77'
SELECTION_COLOR = '#d95f02'
HIGHLIGHT_COLOR = '#003f5c'


app = dash.Dash(__name__, external_stylesheets=["https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"],
                external_scripts=["https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"])
server = app.server

filepath = './dataset/globalterrorismdb_0221dist.csv'
mapbox_access_token = (open(".mapbox_token").read())

td = TerroristData()

# global variables to handle call back between maps


def renderMap(s_dataset, d_dataset, criterium, marker_visible=False, center=None, zoom=1, highlight=None, selectedData=None):
    if not marker_visible:
        if criterium == 'count':
            density_dataset = d_dataset.groupby(
                ['longitude', 'latitude']).size().to_frame(name="count").reset_index()
        elif criterium == 'nkill':
            density_dataset = d_dataset.groupby(
                ['longitude', 'latitude']).nkill.sum().reset_index()
        layer1 = go.Densitymapbox(lon=density_dataset['longitude'], lat=density_dataset['latitude'], z=density_dataset[criterium],
                                  colorscale="Viridis", radius=15, hoverinfo="skip")
        layers = [layer1]

    elif marker_visible:
        s_dataset['color'] = DEFAULT_COLOR
        s_dataset['opacity'] = 0.33
        s_dataset.loc[s_dataset['eventid'].isin(
            selectedData), 'color'] = SELECTION_COLOR
        s_dataset.loc[s_dataset['eventid'].isin(
            selectedData), 'opacity'] = 0.66

        if highlight is not None:
            s_dataset.loc[s_dataset['eventid'].isin(highlight), ['color', 'opacity']] = [
                HIGHLIGHT_COLOR, 1.0]

        customdata = np.stack((s_dataset['eventid'].array, s_dataset['attacktype1_txt'].array, s_dataset['iday'].array,
                               s_dataset['imonth'].array, s_dataset['iyear'].array), axis=-1)

        layer2 = go.Scattermapbox(lon=s_dataset['longitude'], lat=s_dataset['latitude'], marker=dict(
            allowoverlap=True,
            color=s_dataset['color'],
            opacity=s_dataset['opacity']
        ),
            customdata=customdata, hovertemplate="<b>%{customdata[4]}-%{customdata[3]}-%{customdata[2]}</b><br><br>%{customdata[1]}<extra></extra>")
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


def renderweaponChart(dataset, highlight=None):
    if dataset is None:
        fig = go.Figure(data=go.Bar(
            x=None, y=None),
            layout=go.Layout(
            title="Weapon type",
            autosize=True,
            margin=dict(b=10, l=0, r=0, t=40),
            showlegend=False))
        fig.add_annotation(
            text='No data to display. Use the bounding box tool to make a selection on the dotmap.')
        return fig
    dataset['color'] = SELECTION_COLOR
    if highlight is not None:
        dataset.loc[(dataset['weaptype1_txt'] == highlight),
                    ['color']] = HIGHLIGHT_COLOR
    dataset = dataset.sort_values(by=['count'], ascending=False)
    fig = go.Figure(data=go.Bar(
        x=dataset['weaptype1_txt'], y=dataset['count'], text=dataset['count'], marker_color=dataset['color']),
        layout=go.Layout(
        title="Weapon type",
        autosize=True,
        margin=dict(b=10, l=0, r=0),
        showlegend=False))
    fig.update_layout(yaxis=dict(
        title='Count',
        titlefont_size=16,
        tickfont_size=14,
    ))
    return fig


def renderAttackTypeChart(dataset, highlight=None):
    if dataset is None:
        fig = go.Figure(data=go.Bar(
            x=None, y=None),
            layout=go.Layout(
            title="Attack type",
            autosize=True,
            margin=dict(b=10, l=0, r=0, t=40),
            showlegend=False))
        fig.add_annotation(
            text='No data to display. Use the bounding box tool to make a selection on the dotmap.')
        return fig
    dataset['color'] = SELECTION_COLOR
    if highlight is not None:
        dataset.loc[(dataset['attacktype1_txt'] == highlight),
                    ['color']] = HIGHLIGHT_COLOR
    dataset = dataset.sort_values(by=['count'], ascending=False)
    fig = go.Figure(data=go.Bar(
        x=dataset['attacktype1_txt'], y=dataset['count'], text=dataset['count'], marker_color=dataset['color']),
        layout=go.Layout(
        title="Attack type",
        autosize=True,
        margin=dict(b=10, l=0, r=0),
        showlegend=False))
    fig.update_layout(yaxis=dict(
        title='Count',
        titlefont_size=16,
        tickfont_size=14,
    ))
    return fig

def filterDatasetByIds(dataset, ids=[]):
    if len(ids) == 0:
        return dataset
    bool_filter = dataset['eventid'].isin(ids)
    return dataset[bool_filter]


def renderRangeSlider(dataset, val, range):
    fig = go.Figure()
    dataset['color'] = "#25d9a3"
    
    # dataset = dataset.merge(HIGHLIGHTED_ATTACKS, on="date", how='left')
    # dataset.loc[~dataset.summary.isnull(), 'color'] = "#0b4030"

    # customdata = np.stack((dataset['summary'].array,dataset['source'].array,dataset['date'].array), axis=-1)

    fig.add_trace(go.Bar(x=list(dataset['date']), y=list(
        dataset[val]), marker_color=dataset['color']))
    fig.update_layout(
        margin=dict(l=0, r=20, t=60, b=20),
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
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
                    dict(count=20,
                         label="20y",
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
    return fig


def filterDatasetByWeapon(dataset, weapon):
    if dataset is None or weapon is None:
        return dataset
    return_dataset = dataset[dataset.weaptype1_txt == weapon]['eventid']
    return return_dataset


def filterDatasetByAttacktype(dataset, attackType):
    if dataset is None or attackType is None:
        return
    return_dataset = dataset[dataset.attacktype1_txt == attackType]['eventid']
    return return_dataset


def filterDatasetByDateRange(dataset, sliderState):
    if sliderState is not None and 'xaxis.range' in sliderState:
        date_range = [sliderState['xaxis.range']
                      [0], sliderState['xaxis.range'][1]]
    elif sliderState is not None and 'xaxis.range[0]' in sliderState:
        date_range = [sliderState['xaxis.range[0]'],
                      sliderState['xaxis.range[1]']]
    else:
        date_range = DEFAULT_RANGE
    lowerBound = date_range[0].split(' ')[0].split('-')
    lowerBound = datetime(int(lowerBound[0]), int(
        lowerBound[1]), int(lowerBound[2]))
    upperBound = date_range[1].split(' ')[0].split('-')
    upperBound = datetime(int(upperBound[0]), int(
        upperBound[1]), int(upperBound[2]))

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


def intersectHighlights(highlight1, highlight2):
    if highlight1 is not None and highlight2 is not None:
        return list(set(highlight1).intersection(set(highlight2)))
    elif highlight1 is not None and highlight2 is None:
        return highlight1
    elif highlight2 is not None and highlight1 is None:
        return highlight2


df_lat_long = td.get_lat_long()
df_scat = td.get_data_for_scat()
df_country = td.get_country()
df_slider = td.get_aggregated_data_by_month()

mapFig = renderMap(df_scat, df_lat_long, DEFAULT_RADIO_VAL)
weaponChartDataset = td.get_weapon_data().groupby(
    ['weaptype1_txt']).size().to_frame(name="count").reset_index()
weaponChart = renderweaponChart(None)
rangeSliderFig = renderRangeSlider(df_slider, DEFAULT_RADIO_VAL, DEFAULT_RANGE)


df_default_groups = td.get_top_groups_sorted().head(10).gname.tolist()
print("reload")
bb_data = td.get_data_for_bbox_for_ids([])
trace1 = go.Bar(
    x=bb_data["attacktype1_txt"],
    y=bb_data["cnt"],
    marker_color=px.colors.qualitative.Dark24[0],  # color
    textposition="outside",  # text position
    name="Attacks",  # legend name
    customdata=bb_data
)

data = [trace1]  # combine two charts/columns
layout = go.Layout(title="Attacks Type")
fig1 = go.Figure(layout=layout)
fig1.add_annotation(
    text='No data to Display, Please Make selection on scatter plot')
fig1.update_layout(
    title=dict(x=0.5),  # center the title
    xaxis_title="Attack Type",  # setup the x-axis title
    yaxis_title="Count",  # setup the x-axis title
    margin=dict(l=20, r=20, t=60, b=20),  # setup the margin
    paper_bgcolor="aliceblue",  # setup the background color
)
layout = dict(
    xaxis=dict(
        tickmode="array",
        tickvals=bb_data["attacktype1_txt"],
        ticktext=[elem[0:20] for elem in bb_data["attacktype1_txt"]]
    )
)
fig1.update_layout(layout)


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
            html.Div(style={'marginTop': -25}, className='additional-chart col-4',
                     children=[
                         dcc.Graph(id='weapon-chart',
                                   figure=go.Figure(weaponChart)),
                         dcc.Graph(
                             id='attack-type-chart',
                             figure=fig1,
                             # config={"displayModeBar": False},
                         )]),
        ])
    ])

])



@app.callback(Output('attack-type-chart', 'figure'),
              Input('main-map', 'selectedData'),
              Input("attack-type-chart", "clickData"),
              State('main-map', 'selectedData'),
              State('attack-type-chart', 'clickData')
              )
def updateAttackTypeChart(_, __,
                          selectedData,  clickData):
    if selectedData is not None and 'points' in selectedData:
        ids = []
        for point in selectedData['points']:
            ids.append(str(point['customdata'][0]))
        dataset = td.get_attack_type_data(ids)
        dataset = dataset.groupby(['attacktype1_txt']).size().to_frame(
            name="count").reset_index()
        highlight = None
        if clickData is not None:
            highlight = clickData['points'][0]['label']
        return renderAttackTypeChart(dataset, highlight)
    return renderAttackTypeChart(None, None)


@ app.callback(Output('weapon-chart', 'figure'),
               Input('main-map', 'selectedData'),
               Input('weapon-chart', 'clickData'),
               State('main-map', 'selectedData'),
               State('weapon-chart', 'clickData'),
               )
def updateweaponChartAccordingly(_, __,  selectedData, clickData):
    if selectedData is not None and 'points' in selectedData:
        ids = []
        for point in selectedData['points']:
            ids.append(str(point['customdata'][0]))
        dataset = td.get_weapon_data(ids)
        dataset = dataset.groupby(['weaptype1_txt']).size().to_frame(
            name="count").reset_index()
        highlight = None
        if clickData is not None:
            highlight = clickData['points'][0]['label']
        return renderweaponChart(dataset, highlight)
    return renderweaponChart(None, None)



@app.callback(Output('attack-type-chart', 'clickData'),
              Input('attack-type-chart', 'clickData'))
def resetAttackTypeSelectedData(clickData):
    if clickData is not None:
        highlight = clickData['points'][0]['label']
        global SELECTED_ATTACK_TYPE_COLUMN
        if highlight == SELECTED_ATTACK_TYPE_COLUMN:
            SELECTED_ATTACK_TYPE_COLUMN = None
            return None
        SELECTED_ATTACK_TYPE_COLUMN = highlight
        raise PreventUpdate


@app.callback(Output('weapon-chart', 'clickData'),
              Input('weapon-chart', 'clickData'))
def resetWeaponTypeSelectedData(clickData):
    if clickData is not None:
        highlight = clickData['points'][0]['label']
        global SELECTED_WEAPON_TYPE_COLUMN
        if highlight == SELECTED_WEAPON_TYPE_COLUMN:
            SELECTED_WEAPON_TYPE_COLUMN = None
            return None
        SELECTED_WEAPON_TYPE_COLUMN = highlight
        raise PreventUpdate


@app.callback(Output('date-slider', 'figure'),
              Input('deaths-radio', 'value'),
              Input('success-checklist', 'value'),
              State('deaths-radio', 'value'),
              State('date-slider', 'relayoutData'),
              State('success-checklist', 'value'),
              )
def updateSliderAccordingly(_, __, deathsState, sliderState, successState):
    # Extract current date range
    if sliderState is not None and 'xaxis.range' in sliderState:
        range = [sliderState['xaxis.range'][0], sliderState['xaxis.range'][1]]
    elif sliderState is not None and 'xaxis.range[0]' in sliderState:
        range = [sliderState['xaxis.range[0]'], sliderState['xaxis.range[1]']]
    else:
        range = DEFAULT_RANGE
    dataset = td.get_aggregated_data_by_month(successState)
    # Rerender slider based on radio selector value
    fig = renderRangeSlider(dataset, deathsState, range)
    return fig


@ app.callback(Output('main-map', 'figure'),
               Input('main-map', 'relayoutData'),
               Input('date-slider', 'relayoutData'),
               Input('country-dropdown', 'value'),
               Input('success-checklist', 'value'),
               Input('deaths-radio', 'value'),
               Input('weapon-chart', 'clickData'),
               Input("attack-type-chart", "clickData"),
               Input('main-map', 'selectedData'),
               State("main-map", "figure"),
               State('success-checklist', 'value'),
               State('deaths-radio', 'value'),
               State('weapon-chart', 'clickData'),
               State("attack-type-chart", "clickData"),
               State('date-slider', 'relayoutData'),
               State('country-dropdown', 'value'),
               State('main-map', 'selectedData')
               )
def updateMapAccordingly(_, __, ___, ____, _____, ______, _______, ________,
                         mapFigure, successState, deathsState, weaponChartState, attackTypeState, sliderState, countries, mainMapSelectedData):
    ctx = dash.callback_context
    call_bk_item = None
    if ctx.triggered:
        call_bk_item = ctx.triggered[0]['prop_id'].split('.')[0]
    # Filter by year
    df_lat_long_fil = filterDatasetByDateRange(df_lat_long, sliderState)
    df_scat_fil = filterDatasetByDateRange(df_scat, sliderState)
    # Filter by successful/unsuccessful
    df_lat_long_fil = filterDatasetBySuccess(
        df_lat_long_fil, success=successState)
    df_scat_fil = filterDatasetBySuccess(df_scat_fil, success=successState)
    # Filter by countries
    if countries is not None and len(countries) > 0:
        df_scat_fil = df_scat_fil[df_scat_fil.country_txt.isin(countries)]
        df_lat_long_fil = df_lat_long_fil[df_lat_long_fil.country_txt.isin(
            countries)]

    zoom = mapFigure['layout']['mapbox']['zoom']
    center = mapFigure['layout']['mapbox']['center']

    selectedPointIds = []
    highlight = None
    highlight1 = None
    highlight2 = None
    # Highlight the selected
    if mainMapSelectedData != None and mainMapSelectedData['points'] != None and len(
            mainMapSelectedData['points']) != 0:
        # Get all the selected points
        for pt in mainMapSelectedData['points']:
            selectedPointIds.append(pt['customdata'][0])

        highlight_base = filterDatasetByIds(df_scat_fil, selectedPointIds)

        if attackTypeState and 'points' in attackTypeState and attackTypeState['points']:
            attack_type = attackTypeState["points"][0]['label']
            highlight1 = filterDatasetByAttacktype(highlight_base, attack_type)
        if weaponChartState and 'points' in weaponChartState and weaponChartState['points']:
            weapon = weaponChartState["points"][0]['label']
            highlight2 = filterDatasetByWeapon(highlight_base, weapon)

        highlight = intersectHighlights(highlight1, highlight2)

    # Update the map with the existing or new data
    if zoom > 2.5:
        fig = renderMap(df_scat_fil, df_lat_long_fil, deathsState,
                        marker_visible=True, center=center, zoom=zoom, highlight=highlight, selectedData=selectedPointIds)
        return fig
    else:
        return renderMap(df_scat_fil, df_lat_long_fil, deathsState, center=center, zoom=zoom, highlight=highlight, selectedData=selectedPointIds)


if __name__ == '__main__':
    app.run_server(debug=True)
