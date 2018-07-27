import serial
import multiprocessing
import time, csv
import pandas as pd
from os.path import dirname, join

class serialProcess(multiprocessing.Process):

	def __init__(self, input_queue, output_queue, port='/dev/ttyAMA0', baud=115200, idev = 100000, timeout=5, pollspeed=0.1, current_test = ''):
		# Initialises the variables used in this class, baud=, timeout= and pollspeed= can be adjusted
		# But have initial values of 115200, 5 and 0.1 respectively, in the future i could add stopbits and parity here
		multiprocessing.Process.__init__(self)
		self.port = port
		self.baud = baud
		self.ID = idev
		self.timeout = timeout
		self.pollspeed = pollspeed
		self.input_queue = input_queue
		self.output_queue = output_queue
		# self.run = False
		self.serial_is_open = False
		self.serial = []
		self.df = []
		self.data = []
		self.current_test = current_test

	def open_serial(self):
		self.serial = serial.Serial(self.port, self.baud, timeout=1)
		self.serial_is_open = True
		print 'Serial Port ' + self.port + ' opened'


	def close_serial(self):
		"""stops running thread"""

		self.serial.close()
		self.serial_is_open = False

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

	def monitor_sensors(self):
		index = -1
		while True:
			buffer = self.serial.inWaiting()
			if buffer != '':
				_data = self.readSerial(1)
				try:
					index = index + 1
					_data_tokenized =  _data.strip().split('\t')
					print _data_tokenized

					if _data_tokenized != ['']: 
						_data_tokenized[0] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
						csv_Path = join(self.current_test, self.port.replace('/','_') + '_log.csv')
						with open(csv_Path, "a") as csv_File:
							wr = csv.writer(csv_File)
							wr.writerow(_data_tokenized)

				except:
					pass

	def run(self):

	   	while True:

	   		if not self.input_queue.empty():
		   		task = self.input_queue.get()
		   		
		   		if task == "READ":

		   			if not self.serial_is_open:
		   				print 'Serial Port ' + self.port + ' is closed - > open' 
		   				self.open_serial()

					self.flush()
					print '-------------------------------'
					print '-----Running READ SENSORS------'
					print '-------------------------------'

					## Turn everything off from shell mode
					## Turn everything off from shell mode
					self.writeSerial('shell -on\r')
					self.readSerial(2)
					self.writeSerial('esp off\r')
					self.readSerial(2)
					self.writeSerial('shell -on\r')
					self.readSerial(4)
					self.writeSerial('monitor\r')
					
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
					print '-----Monitoring Sensors-----'
					self.monitor_sensors()

				if task == "STOP":
					self.close_serial()
					self.run = False
					break