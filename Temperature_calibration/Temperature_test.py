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

PORT = '/dev/cu.usbmodem1411'
PORT_CURRENT = '/dev/cu.usbmodem1421'
BAUDRATE = 115200

reading_interval = 2
interval_on_off = 60*30
number_iter = 5
limit_ESP_ON = 5 # secs
limit_ESP_OFF = 30 # secs

test_file = ("LogTemp" + str(datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S"))+'.csv')
test_file_current = ("LogTempCurrent" + str(datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S"))+'.csv')
file_path = dirname(__file__)
index = -1
Time=[]
Delta=[]
Temp=[]
Ext_Temp=[]
Hum=[]
Ext_Hum=[]

class testSequencer(multiprocessing.Process):

	def __init__(self, input_queue, output_queue, port='/dev/ttyAMA0', baud=115200):

		multiprocessing.Process.__init__(self)
		self.PORT = port
		self.BAUDRATE = baud
		self.input_queue = input_queue
		self.output_queue = output_queue
		self.serial_open = False
		self.serial = []
		self.df = pd.DataFrame(
			{'Time':[],
			'Temp': [],
			'Ext_Temp':  [],
			'Hum': [],
			'Ext_Hum': [],
			'Comment': []})

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

	def check_stability(self, name, thd):
		if len(self.df.loc[:,name]) > 20:
			b, a = signal.ellip(4, 0.01, 120, 0.125)  # Filter to be applied.
			_filter = signal.filtfilt(b, a, self.df.loc[:,name])
			## We say that the signal is stable if the difference is below 0.5degC
			stability = abs(self.df.loc[:,name]-_filter) < thd
			print self.df.loc [:,name] + '\t' + _filter
		else:
			stability = False
		return stability

	def perform_test(self, comment, file, interval_limit):
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
							
						with open(file, "a") as csv_File:
							if (time.time() - time_last > reading_interval):
								time_last = time.time()
								wr = csv.writer(csv_File)
								wr.writerow(_data_tokenized)
								# self.output_queue.put(_data_tokenized)

				except:
					if serial_open == False: break
					pass

	def perform_test_altern(self, file, ESP_INIT, interval_limit):
		index = -1
		time_last = 0
		time_last_onoff = time.time()
		status = ''

		if ESP_INIT == 'ON':
			time_ESP_ON = time.time()
			time_ESP_OFF = 0
			status = 'ESP_ON'
		elif ESP_INIT == 'OFF':
			time_ESP_OFF = time.time()
			time_ESP_ON = 0
			status = 'ESP_OFF'

		while (time.time() - time_last_onoff < interval_limit) and self.input_queue.empty():
			buffer = self.serial.inWaiting()
			if (status == 'ESP_ON') and (time.time()-time_ESP_ON > limit_ESP_ON):
				self.writeSerial('shell -on\r')
				self.readSerial(2)
				self.writeSerial('esp -off\r')
				self.readSerial(4)
				self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
				self.readSerial(4)
				status = 'ESP_OFF'
				time_ESP_OFF = time.time()
				time_ESP_ON = 0
				print 'Turning ESP OFF at {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			
			if (status == 'ESP_OFF') and (time.time()-time_ESP_OFF > limit_ESP_OFF):
				self.writeSerial('shell -on\r')
				self.readSerial(2)				
				self.writeSerial('esp -on\r')
				self.readSerial(4)
				self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
				self.readSerial(4)
				status = 'ESP_ON'
				time_ESP_ON = time.time()
				time_ESP_OFF = 0
				print 'Turning ESP ON at {}'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


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
						with open(file, "a") as csv_File:
							if (time.time() - time_last > reading_interval):
								time_last = time.time()
								wr = csv.writer(csv_File)
								wr.writerow(_data_tokenized)
								# self.output_queue.put(_data_tokenized)

				except:
					if serial_open == False: break
					pass

	def run(self):

		while True:

			if not self.input_queue.empty():
		   		task = self.input_queue.get()

				if task == '1':
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True

					self.flush()
					print '------------------------------'
					print ' Running Task 1'
					print '------------------------------'

					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable carbon\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable nitro\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Carbon monoxide resistance\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Nitrogen dioxide resistance\r')
					self.readSerial(2)
					self.writeSerial('esp -off\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)

					print 'Getting Header'
 
					if os.path.isfile(test_file) == False: 
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

						self.output_queue.put(_header)

					## Perform Test
					print 'Performing Test Number 1'
					self.perform_test('Test 1: ALL OFF', test_file, interval_on_off)

					## Once temperature is stable, close serial
					self.close_serial()
					self.serial_open = False

					print 'Test Number 1 Finished'

				elif task == '2':
					print '------------------------------'
					print ' Running Task 2'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True

					self.flush()
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable carbon\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable nitro\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Carbon monoxide resistance\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Nitrogen dioxide resistance\r')
					self.readSerial(2)
					self.writeSerial('esp -on\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)		

					if os.path.isfile(test_file) == False:
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					print 'Performing Test Number 2'
					self.perform_test('Test 2: ESP ON', test_file, interval_on_off)

					## Once temperature is stable, close serial
					self.close_serial()
					self.serial_open = False
					print 'Test Number 2 Finished'

				elif task == '3':
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()
					print '------------------------------'
					print ' Running Task 3'
					print '------------------------------'
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -enable carbon\r')
					self.readSerial(2)
					self.writeSerial('esp -off\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)

					if os.path.isfile(test_file) == False:
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					## Perform Test
					print 'Performing Test Number 3'
					self.perform_test('Test 3: MICS ON', test_file, interval_on_off)

					## Once temperature is stable, close serial
					self.close_serial()
					self.serial_open = False
					print 'Test Number 3 Finished'

				elif task == '4':
					print '------------------------------'
					print ' Running Task 4'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -enable carbon\r')
					self.readSerial(2)
					self.writeSerial('esp -on\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)

					if os.path.isfile(test_file) == False: 
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					## Perform Test
					print 'Performing Test Number 4'
					self.perform_test('Test 4: ALL ON', test_file, interval_on_off)

					## Once temperature is stable, close serial
					self.close_serial()
					self.serial_open = False
					print 'Test Number 4 Finished'

				elif task == '5':
					print '------------------------------'
					print ' Running Task 5'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()

					if os.path.isfile(test_file) == False:
						_header = ['Time', 'Current']
						with open(test_file_current, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
								print '-----Header 5 Writen-----'

					self.perform_test('Test 5: CURRENT LOG', test_file_current, -1)
				
				elif task == '6':
					print '------------------------------'
					print ' Running Task 6'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable carbon\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable nitro\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Carbon monoxide resistance\r')
					self.readSerial(2)
					self.writeSerial('sensor -disable Nitrogen dioxide resistance\r')
					self.readSerial(2)
					self.writeSerial('esp -off\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)

					if os.path.isfile(test_file) == False: 
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'

					self.perform_test_altern(test_file, 'OFF', interval_on_off)

				elif task == '7':
					print '------------------------------'
					print ' Running Task 7'
					print '------------------------------'
					self.serial = serial.Serial(self.PORT, self.BAUDRATE, timeout = 1)
					self.serial_open = True
					self.flush()
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('sensor -enable carbon\r')
					self.readSerial(2)
					self.writeSerial('esp -off\r')
					self.readSerial(4)
					self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
					self.readSerial(1)

					if os.path.isfile(test_file) == False: 
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
							with open(test_file, "wb") as csv_File:
								wr = csv.writer(csv_File)
								wr.writerow(_header)
							print '-----Header Writen-----'
					for i in range(number_iter + 1):
						## Alternating ON

						self.perform_test_altern(test_file, 'OFF', interval_on_off)

						## All off
						self.writeSerial('shell -on\r')
						self.readSerial(2)
						self.writeSerial('sensor -disable carbon\r')
						self.readSerial(2)
						self.writeSerial('sensor -disable nitro\r')
						self.readSerial(2)
						self.writeSerial('sensor -disable Carbon monoxide resistance\r')
						self.readSerial(2)
						self.writeSerial('sensor -disable Nitrogen dioxide resistance\r')
						self.readSerial(2)
						self.writeSerial('esp -off\r')
						self.readSerial(4)
						self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
						self.readSerial(4)
						self.perform_test('ALL OFF', test_file, interval_on_off)

						self.writeSerial('shell -on\r')
						self.readSerial(2)
						self.writeSerial('sensor -enable carbon\r')
						self.readSerial(2)
						self.writeSerial('esp -off\r')
						self.readSerial(4)
						self.writeSerial('monitor temp, ext temp, hum, ext hum\r')
						self.readSerial(4)

				elif task == 'STOP':
					self.close_serial()



app.layout = html.Div(children=[
	html.Div([
		dcc.Markdown(children='## Temperature Calibration'),	
		html.Button(id='test-1-run', type='submit', children='TURN ALL OFF'),
		html.Div(id='test-1-result'),
		html.Button(id='test-2-run', type='submit', children='ESP ONLY'),
		html.Div(id='test-2-result'),
		html.Button(id='test-3-run', type='submit', children='MICS ONLY'),
		html.Div(id='test-3-result'),
		html.Button(id='test-4-run', type='submit', children='MICS / ESP ON'),
		html.Div(id='test-4-result'),
		html.Button(id='test-5-run', type='submit', children='MICS OFF / ESP ON - OFF Sequence'),
		html.Div(id='test-5-result'),
		html.Button(id='test-6-run', type='submit', children='MICS ON - OFF Sequence / ESP ON - OFF Sequence'),
		html.Div(id='test-6-result'),
		html.Button(id='stop', type='submit', children='STOP'),
		html.Div(id='stop-result'),
		], className='row'),

	html.Div([
		dcc.Graph(id='Current-Graph', style={'height': 400}, animate = False),
	]),
	
	html.Div([
		dcc.Graph(id='Temperature-Graph', style={'height': 400}, animate = False),
	]),

	html.Div([
		dcc.Graph(id='Humidity-Graph', style={'height': 400}, animate = False),
	]),
		
	## Interval from graph Update
	dcc.Interval(
		id='interval-component',
		interval=1*1000,
		n_intervals=0
	),

])


@app.callback(Output('Current-Graph','figure'),
  [Input('interval-component','n_intervals')])
def update_graph_live(n):

	dataCurrent = pd.read_csv(join(file_path, test_file_current), delimiter = ',', encoding="utf-8-sig").set_index('Time')
	dataCurrent = dataCurrent.tail(1000)
	Current = dataCurrent.loc[:,'Current']

	traces = list()
	traces.append(go.Scatter(
		x=dataCurrent.index,
		y=Current,
		name='Current'
	))

	layout = go.Layout(
		 showlegend=True,
		 legend=go.Legend(
			 x=0,
			 y=1.5
		 ),
	)

	return {'data': traces, 'layout': layout}


@app.callback(Output('Temperature-Graph','figure'),
  [Input('interval-component','n_intervals')])
def update_graph_live(n):

	dataVal = pd.read_csv(join(file_path, test_file), delimiter = ',', encoding="utf-8-sig").set_index('Time')
	dataVal = dataVal.tail(1000)

	Temperature = dataVal.loc[:,'Temperature']
	Ext_temperature = dataVal.loc[:,'External Temperature']

	traces = list()
	traces.append(go.Scatter(
		x=dataVal.index,
		y=Temperature,
		name='Temperature'
	))

	traces.append(go.Scatter(
		x=dataVal.index,
		y=Ext_temperature,
		name='External Temperature'
	))

	layout = go.Layout(
		 showlegend=True,
		 legend=go.Legend(
			 x=0,
			 y=1.5
		 ),
	)

	return {'data': traces, 'layout': layout}

@app.callback(Output('Humidity-Graph','figure'),
  [Input('interval-component','n_intervals')])
def update_graph_live(n):

	# dff = pd.read_json(dataVal, index ='Time')
	dataVal = pd.read_csv(join(file_path, test_file), delimiter = ',',  encoding="utf-8-sig").set_index('Time')
	dataVal = dataVal.tail(1000)

	Humidity = dataVal.loc[:,'Humidity']
	Ext_humidity = dataVal.loc[:,'External Humidity']

	traces = list()
	traces.append(go.Scatter(
		x=dataVal.index,
		y=Humidity,
		name='Humidity'
	))

	traces.append(go.Scatter(
		x=dataVal.index,
		y=Ext_humidity,
		name='External Humidity'
	))

	layout = go.Layout(
		 showlegend=True,
		 legend=go.Legend(
			 x=0,
			 y=1.5
		 ),
	)

	return {'data': traces, 'layout': layout}


@app.callback(Output('test-1-result', 'children'), 
	[Input('test-1-run', 'n_clicks')])
def onclick(n):
	print 'DEBUG: HIT BUTTON 1'
	if n>1:
		input_queue.put('1')
		input_queue2.put('5')

@app.callback(Output('test-2-result', 'children'), 
	[Input('test-2-run', 'n_clicks')])
def onclick(n):
	if n>1:
		input_queue.put('2')
		input_queue2.put('5')

@app.callback(Output('test-3-result', 'children'), 
	[Input('test-3-run', 'n_clicks')])
def onclick(n):
	if n>1:
		input_queue.put('3')
		input_queue2.put('5')


@app.callback(Output('test-4-result', 'children'), 
	[Input('test-4-run', 'n_clicks')])
def onclick(n_clicks):
	if n_clicks>1:
		input_queue.put('4')
		input_queue2.put('5')

@app.callback(Output('test-5-result', 'children'), 
	[Input('test-5-run', 'n_clicks')])
def onclick(n_clicks):
	if n_clicks>1:
		input_queue.put('6')
		input_queue2.put('5')

@app.callback(Output('test-6-result', 'children'), 
	[Input('test-6-run', 'n_clicks')])
def onclick(n_clicks):
	if n_clicks>1:
		input_queue.put('7')
		input_queue2.put('5')


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
	worker1 = testSequencer(input_queue, output_queue, PORT, BAUDRATE)
	worker1.daemon = True
	worker1.start()

	worker2 = testSequencer(input_queue2, output_queue2, PORT_CURRENT, BAUDRATE)
	worker2.daemon = True
	worker2.start()

	## Dash over Flask
	app.run_server(debug=True, host='0.0.0.0', port=8000, processes = 4)





