import numpy as np
from time import sleep
import serial
import plotly
import plotly.graph_objs as go
import plotly.tools as tls
from scipy import signal
import pandas as pd
import datetime
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
from os.path import dirname, join
import csv
import os.path

from multiprocessing import Process, Queue, current_process, freeze_support
import multiprocessing
input_queue = Queue()
output_queue = Queue()
input_queue2 = Queue()
output_queue2 = Queue()

app = dash.Dash()
server = app.server

PORT_KIT1 = '/dev/cu.usbmodem1421'
PORT_KIT2 = '/dev/cu.usbmodem1411'
BAUDRATE = 115200

reading_interval = 0.1

time_both_on = 180
# list_time_altern = [0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 8, 8, 8, 8, 8]
list_time_altern = [8,8,8,8,8,10,10,10,10,10,12,12,12,12,14,14,14,14,14,16,16,16,16,16,18,18,18,18,18,20,20,20,20,20]

time_rest = 30

test_kit1 = ("LogKit1" + str(datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S"))+'.csv')
test_kit2 = ("LogKit2" + str(datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S"))+'.csv')
file_path = dirname(__file__)
index = -1

class testSequencer(multiprocessing.Process):

	def __init__(self, input_queue, output_queue, test_file, port='/dev/ttyAMA0', baud=115200):

		multiprocessing.Process.__init__(self)
		self.PORT = port
		self.BAUDRATE = baud
		self.input_queue = input_queue
		self.output_queue = output_queue
		self.serial_open = False
		self.test_file = test_file
		self.serial = []
		self.df = pd.DataFrame(
			{'Time':[],
			'PM2.5': [],
			'PM5':  [],
			'PM10': [],
			})

	def close_serial(self):
		if self.serial_open == True:
			self.serial_open = False
			self.serial.close()

	def writeSerial(self, data):
		self.serial.write(data)
		
	def readSerial(self, lines):

		if lines == 1:
			return self.serial.readline().replace("\r", "")
		else:
			for i in range(lines):
				self.serial.readline().replace("\r", "")
			return ''

	def flush(self):
		self.serial.flushInput()
		self.serial.flushOutput()

	def perform_test(self, comment, interval_limit):
		index = -1
		time_last = 0
		if interval_limit == -1:
			time_last_onoff = 0
			time_mult = -1
			interval_limit = 0
		else:
			time_mult = 1 
			time_last_onoff = time.time()

		while (time.time()*time_mult - time_last_onoff < interval_limit) and self.input_queue.empty():
			buffer = self.serial.inWaiting()
			if buffer != '':
				_data = self.readSerial(1)
				try:
					index = index + 1
					_data_tokenized =  _data.strip().split('\t')

					if _data_tokenized != ['']:
						if len(_data_tokenized) == 1:
							_data_tokenized = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), _data_tokenized[0]]
						else:
							_data_tokenized[0] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")	
							
						with open(self.test_file, "a") as csv_File:
							if (time.time() - time_last > reading_interval):
								time_last = time.time()
								wr = csv.writer(csv_File)
								wr.writerow(_data_tokenized)
								# self.output_queue.put(_data_tokenized)

				except:
					if self.serial_open == False: break
					pass

	def run(self):
		monitor_sentence = 'monitor PM 1.0, PM 2.5, PM 10.0\r'
		while True:

			if not self.input_queue.empty():
		   		task = self.input_queue.get()

				if task == '1':

					print '------------------------------'
					print ' Running Task 1'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()

					## Turn everything off from shell mode
					# self.writeSerial('shell -on\r')
					# self.readSerial(2)
					self.writeSerial(monitor_sentence)
					self.readSerial(1)

					if os.path.isfile(self.test_file) == False: 
						_Bheader = self.readSerial(1)
						_header = _Bheader.strip().split('\t')
						print _header[0]
						while _header[0] != 'Time':
							_Bheader = self.readSerial(1)
							_header = _Bheader.strip().split('\t')
						# _header_cor = ['hello{0}'.format(i) for i in _header]
						print 'Header for ' + self.PORT + ' sensors'
						print _header

						if _header != '': 
							with open(self.test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					self.perform_test('BOTH ON', time_both_on)

					for i in list_time_altern:

						## All off
						self.writeSerial('shell -on\r')
						self.readSerial(2)
						self.writeSerial('sensor -disable pm 1\r')
						self.readSerial(6)

						self.perform_test('ONE OFF', time_rest)

						self.writeSerial('sensor -enable pm 1\r')
						self.readSerial(6)

						time_enable = time.time()
						while (time.time()-time_enable < 2):
							print 'Waiting during 2s'
						self.writeSerial(monitor_sentence)
						self.readSerial(4)

						self.perform_test('BOTH ON', i)

				if task == '2':
					
					print '------------------------------'
					print ' Running Task 2'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()

					## Turn everything off from shell mode
					# self.writeSerial('shell -on\r')
					# self.readSerial(2)
					self.writeSerial(monitor_sentence)
					self.readSerial(1)

					if os.path.isfile(self.test_file) == False: 
						_Bheader = self.readSerial(1)
						_header = _Bheader.strip().split('\t')
						print _header[0]
						while _header[0] != 'Time':
							_Bheader = self.readSerial(1)
							_header = _Bheader.strip().split('\t')
						# _header_cor = ['hello{0}'.format(i) for i in _header]
						print 'Header for ' + self.PORT + ' sensors'
						print _header

						if _header != '': 
							with open(self.test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					total_time = time_both_on + np.sum(list_time_altern) + len(list_time_altern)*time_rest

					self.perform_test('BOTH ON', total_time)

				elif task == 'STOP':
					self.close_serial()

app.layout = html.Div(children=[
	html.Div([
		dcc.Markdown(children='## Particle Sensor Wake Up Test'),	
		html.Button(id='test-1-run', type='submit', children='Perform test'),
		html.Div(id='test-1-result'),
		html.Button(id='stop', type='submit', children='STOP'),
		html.Div(id='stop-result'),
		], className='row'),

	html.Div([
		dcc.Graph(id='Kit1-Graph', style={'height': 400}, animate = False),
	]),
	
	html.Div([
		dcc.Graph(id='Kit2-Graph', style={'height': 400}, animate = False),
	]),
		
	## Interval from graph Update
	dcc.Interval(
		id='interval-component',
		interval=1*1000,
		n_intervals=0
	),

])

@app.callback(Output('Kit1-Graph','figure'),
  [Input('interval-component','n_intervals')])
def update_graph_live(n):

	file_csv = join(file_path, test_kit1)
	traces = list()
	layout = go.Layout(
	 showlegend=True)

	layout.legend = go.layout.Legend(
		x=0,
		y=1.5
	)

	if (os.path.exists(file_csv)):

		dataKit1 = pd.read_csv(file_csv, delimiter = ',', encoding="utf-8-sig").set_index('Time')
		dataKit1 = dataKit1.tail(1000)
		PM1= dataKit1.loc[:,'PM 1.0']
		PM25 = dataKit1.loc[:,'PM 2.5']
		PM10 = dataKit1.loc[:,'PM 10.0']

		traces.append(go.Scatter(
			x=dataKit1.index,
			y=PM1,
			name='PM1'
		))
		
		traces.append(go.Scatter(
			x=dataKit1.index,
			y=PM25,
			name='PM2.5'
		))

		traces.append(go.Scatter(
			x=dataKit1.index,
			y=PM10,
			name='PM10'
		))


	return {'data': traces, 'layout': layout}


@app.callback(Output('Kit2-Graph','figure'),
  [Input('interval-component','n_intervals')])
def update_graph_live(n):

	file_csv = join(file_path, test_kit2)
	traces = list()
	layout = go.Layout(
	 showlegend=True)

	layout.legend = go.layout.Legend(
		x=0,
		y=1.5
	)

	if (os.path.exists(file_csv)):

		dataKit2 = pd.read_csv(file_csv, delimiter = ',', encoding="utf-8-sig").set_index('Time')
		dataKit2 = dataKit2.tail(1000)
		PM1 = dataKit2.loc[:,'PM 1.0']
		PM25 = dataKit2.loc[:,'PM 2.5']
		PM10 = dataKit2.loc[:,'PM 10.0']

		traces.append(go.Scatter(
			x=dataKit2.index,
			y=PM1,
			name='PM1'
		))
		
		traces.append(go.Scatter(
			x=dataKit2.index,
			y=PM25,
			name='PM2.5'
		))

		traces.append(go.Scatter(
			x=dataKit2.index,
			y=PM10,
			name='PM10'
		))

	return {'data': traces, 'layout': layout}

@app.callback(Output('test-1-result', 'children'), 
	[Input('test-1-run', 'n_clicks')])
def onclick(n):
	print 'DEBUG: HIT BUTTON 1'
	if n>1:
		# Run Sequence 1 permantent, 2 altern
		input_queue.put('1')
		input_queue2.put('2')
		# Run Sequence 2 permantent, 1 altern
		# input_queue.put('2')
		# input_queue2.put('1')


@app.callback(Output('stop-result', 'children'), 
	[Input('stop', 'n_clicks')])
def onclick(n):
	if n>0:
		input_queue.put('STOP')
		input_queue2.put('STOP')

# CSS	
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

app.scripts.config.serve_locally = True

# Port
if __name__ == '__main__':

	## Port 1 for 
	worker1 = testSequencer(input_queue, output_queue, test_kit1, PORT_KIT1, BAUDRATE)
	worker1.daemon = True
	worker1.start()

	worker2 = testSequencer(input_queue2, output_queue2, test_kit2, PORT_KIT2, BAUDRATE)
	worker2.daemon = True
	worker2.start()

	## Dash over Flask
	app.run_server(debug=True, host='0.0.0.0', port=8000, processes = 4)





