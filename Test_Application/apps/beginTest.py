# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
from os.path import dirname, join
import datetime, os
from app import app

import json

layout = html.Div([
    dcc.Markdown('#### Configure Test Session'),

    html.Div([
        dcc.Markdown('**Test Name**'),

        dcc.Input(id = "test_name",
            placeholder='Enter test name',
            type='text'
        ),

    ]),

    html.Br(),

    html.Div([
        dcc.Markdown('**Test Purpose**'),
        dcc.Input(id = "test_purpose",
            placeholder='Enter test purpose',
            type='text'
        ),
    ]),

    html.Br(),

    html.Div([
        dcc.Markdown('**Test Comment**'),
        dcc.Textarea(id = "test_comment",
            placeholder='Enter test comment'
        ),
    ]),

    html.Br(),
    html.Div([
        html.Button(id='create-test', n_clicks=0, children='Create Test Session'),
    ]),

    html.Br(),

    html.Div(id = 'button-output'),

    html.Br(),
    dcc.Link('Launch!', href='/apps/runTest')
],style={'color': 'grey', 'textAlign': 'center'})

@app.callback(Output('button-output', 'children'),
              [Input('create-test', 'n_clicks')],
              [State('test_name', 'value'),
               State('test_comment', 'value'),
               State('test_purpose', 'value')])
def create_test_sess(n_clicks, test_name, test_comment, test_purpose):
    if n_clicks > 0:
        # Create folder structure under data subdir
        newpath = join(dirname(__file__), 'data', datetime.datetime.now().strftime("%Y-%m-%d"), test_name)
        
        if not os.path.exists(newpath):
            os.makedirs(newpath)

            # Create json file for test description
            data_json = {}
            data_json['test_name'] = test_name
            data_json['test_comment'] = test_comment
            data_json['test_purpose'] = test_purpose
            data_json['test_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_json['test_full_ID'] = (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '-' + test_name)
            with open(join(newpath, 'test_description.json'), 'w') as json_file:
                json.dump(data_json, json_file)

            with open(join(dirname(__file__), 'data', 'current_test.txt'), 'w') as current_test:
                current_test.write(join(datetime.datetime.now().strftime("%Y-%m-%d"),test_name))

        return 'Test created with name {}'.format(test_name)