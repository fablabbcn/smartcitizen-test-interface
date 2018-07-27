# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
import colorlover as cl
import plotly
import plotly.graph_objs as go

# Numpy and data treatment
import numpy as np
import pandas as pd
import io, os, time, datetime
from os.path import dirname, join

# Import Application
from app import app

## MultiProcess stuff
from multiprocessing import Process, Queue, current_process, freeze_support

## Inter Scripts
from scripts.serialports import *
from scripts.serialworker import serialProcess
from scripts.i2cworker import i2cProcess
from scripts.readcsv  import *

## --- Serial Stuff
SERIAL_BAUD = 115200
SERIAL_ID = '123456'
TIME_OUT = 5
POLLSPEED = 1
input_queue = Queue()
output_queue = Queue()

##---  I2C Sensors
# Adafruit
# sht31_sens = SHT31(address = 0x44)
# Psens
address_p_sens = 0x13
packet_p_sens = 2
POLLSPEED_P_SENS = 5
I2Csensors = list(['Pressure Sensor', 'SHT31'])
address_pump = 0x14

global_md = '''
### Dashboard Sensors
'''

column1_md = '''
### Serial devices here
'''

column2_md = '''
### I2C devices here
'''

# ColorScale (TODO)
colorscale = cl.scales['9']['qual']['Paired']

# Sample CSV Read to kick things off
# filename = '18-06-07.csv'
# dataset = readcsv(filename, join(dirname(__file__),'data'))
# names = list(dataset.columns)
# dataset2save = join(dirname(__file__),'data/','data.csv')

layout = html.Div([

	dcc.Link('Back to Config', href='/apps/beginTest'),
	dcc.Markdown(children=global_md),


	html.Div([
		html.Div([
			html.Button(id='test-run', type='submit', children='Start'),
			html.Div(id='test-result'),
			html.Button(id='test-stop', type='submit', children='Stop'),
			html.Div(id='test-stop-output'),

		],style = dict(
        	width = '30%',
        	display= 'inline-block',
        	),),
		
		html.Div([
			dcc.Markdown(['Pump Control']),
			dcc.RadioItems(
				id='pump-control-ri',
				options=[{'label': 'ON', 'value': 'ON'},{'label': 'OFF', 'value': 'OFF'}],
				value='OFF',
				labelStyle={'display': 'inline-block'}
			),

			html.Div(id='pump-control'),
		], style = dict(
	        width = '30%',
	        display= 'inline-block',
	        verticalAlign = "middle",
	        textAlign = 'center')
		,)

	], style = dict(
        width = '50%',
        display= 'inline-block',
        verticalAlign = "middle"
    ),),

	html.Div([

		html.Div([
			
			dcc.Markdown(children=column1_md),
			dcc.Dropdown(id='dropdown-serial', multi=True),
			# 	options=[{'value': serialsensors[0], 'label':serialsensors[0]} for serialsensors in zip(dataset.columns)]),
			dcc.Graph(id='graph-serial', 
				animate = False,
			),
			dcc.Interval(id='interval-component-serial',
				interval=1*2000,
				n_intervals=0),
		], className="six columns"),
		
		html.Div([
			dcc.Markdown(children=column2_md),
			dcc.Dropdown(id='dropdown-i2c', multi=True),
				# options=[{'value': i2csensors[0], 'label':i2csensors[0]} for i2csensors in zip(I2Csensors)]),
			dcc.Graph(id='graph-i2c', 
				animate = False,
			),
			dcc.Interval(id='interval-component-i2c',
				interval=1*2000,
				n_intervals=0),
			], className="six columns"),
			
	],)
	])



# ## Serial
# @app.callback(Output('graph-serial','figure'),
# 	[Input(component_id = 'interval-component-serial',component_property='n_intervals'),
#	 Input(component_id = 'dropdown-serial', component_property = 'value')
#	 ])
# def update_serial_live(n, selected_drop_downs):

#	 # Read CSV and select the drop down items only
#	 dataset = readcsv(filename, join(dirname(__file__),'data'))
#	 plot_data = dataset.loc[:,selected_drop_downs]

#	 # Only make this if there is actually stuff to process, skip otherwise
#	 traces = list()
#	 if len(selected_drop_downs)>0:
#		 for value in enumerate(selected_drop_downs):
#			 traces.append(plotly.graph_objs.Scatter(
#				 x=plot_data.index,
#				 y=plot_data.loc[:,value[1]],
#				 name=(value[1]),
#				 mode= 'lines',
#				 )
#			 )
#		 layout = go.Layout(
#			 showlegend=True,
#			 legend=go.Legend(
#				 x=0,
#				 y=1.5
#			 ),
#		 )
#	 return {'data': traces, 'layout': layout}

# ## I2C
# @app.callback(Output('graph-i2c','figure'),
#	 [Input(component_id = 'interval-component-i2c',component_property='n_intervals'),
#	 Input(component_id = 'dropdown-i2c', component_property = 'value')
#	 ])
# def update_i2c_live(n, selected_drop_downs):

#	 # Read CSV and select the drop down items only
#	 dataset = readcsv(filename, join(dirname(__file__),'data'))
#	 plot_data = dataset.loc[:,selected_drop_downs]

#	 # Only make this if there is actually stuff to process, skip otherwise
#	 traces = list()
#	 if len(selected_drop_downs)>0:
#		 for value in enumerate(selected_drop_downs):
#			 traces.append(plotly.graph_objs.Scatter(
#				 x=plot_data.index,
#				 y=plot_data.loc[:,value[1]],
#				 name=(value[1]),
#				 mode= 'lines',
#				 )
#			 )
#		 layout = go.Layout(
#			 showlegend=True,
#			 legend=go.Legend(
#				 x=0,
#				 y=1.5
#			 ),
#		 )

#	 return {'data': traces, 'layout': layout}

# @app.callback(Output('pump-control','children'), 
# 	[Input('pump-control-ri', 'value')])
# def on_click(value):
# 	print 'pump control is ' + value
# 	if (value == 'ON'):
# 		# i2cdevice_write(pump_device, 10)
# 		pump_worker.write(10) 
# 	if (value == 'OFF'): 
# 		# i2cdevice_write(pump_device, 0)
# 		pump_worker.write(0) 

@app.callback(Output('test-result', 'children'), 
	[Input('test-run', 'n_clicks')])
def onclick(n):
	if (n>0): 
		print 'DEBUG: callback hit Test Run'
		with open(join(dirname(__file__), 'data', 'current_test.txt'), 'r') as current_test_file:
			current_test=join(dirname(__file__), 'data', current_test_file.read())
		
		serial_workers = [serialProcess(input_queue, output_queue, port, SERIAL_BAUD, SERIAL_ID, TIME_OUT, POLLSPEED, current_test) for port in serialports()]
		for worker in serial_workers:
			print worker.name
			worker.daemon = True
			worker.start()
		
		print 'Serial Workers'
		print serial_workers

		input_queue.put('READ')

		# sensors_read(pressure_sens, sht31_sens, serial_devices)

@app.callback(Output('test-stop-output', 'children'), 
	[Input('test-stop', 'n_clicks')])
def onclick(n):
	if (n>0): 
		print 'DEBUG: callback hit Test Stop'
		input_queue.put('STOP')
