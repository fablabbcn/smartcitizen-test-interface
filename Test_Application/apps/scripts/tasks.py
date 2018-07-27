import datetime
import time
import os
from celery import Celery
from I2Cdevice import *
import serial
# from scripts.Adafruit_STH31 import *

celery_app = Celery('tasks', 
    backend='rpc://', 
    broker='pyamqp://guest@localhost//')

# @celery_app.task
# def hello():
#     # time.sleep(10)
#     with open ('hellos.txt', 'a') as hellofile:
#         hellofile.write('Hello {}\n'.format(datetime.datetime.now()))

# @celery_app.task
# def goodbye():
# 	with open ('hellos.txt', 'a') as hellofile:
# 		hellofile.write('Goodbye {}\n'.format(datetime.datetime.now()))

# Sensors ALL
@celery_app.task
def serial_open(_serial_device):
	_sps = []
	SERIAL_PORT = _serial_device [0]
	SERIAL_BAUDRATE = _serial_device [1]
	SERIAL_ID = _serial_device[2]
	_serial = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)
	_sps.append((SERIAL_PORT, SERIAL_BAUDRATE, SERIAL_ID, _serial))
	print 'Serial Open OK'

	return _sps

# @celery_app.task
# def serial_init(_serial_objects):

# 	for _object in _serial_objects:
# 		print 'Initialising '
# 		print _object
# 		_object.flushInput()
# 		# time.sleep(5)
# 		serial_dev_write(_object, 'outlevel 1\r\n')
# 		print _object.readline()
# 		print _object.readline()
# 		serial_dev_write(_object, 'monitor\r\n')
# 		print _object.readline()
# 		print _object.readline()
# 		_header = _object.readline().strip().split(', ')
# 		print _header
# 	return _header

@celery_app.task
def sensors_stop(_serial_devices):
	_result_serial = list()
	for _object in [column[0][3] for column in _serial_devices]:
		_object.write('\r\n')

@celery_app.task
def sensors_read(_I2Cdevice, _serial_devices):
# def sensors_read(_I2Cdevice, _sht31device, _serial_devices):
	print 'Read called'
	_result_serial = list()
	_header_full = []
	# Put all serials into monitor mode
	for _object in [column[0][3] for column in _serial_devices]:
		print 'Initialising '
		print _object
		_object.flushInput()
		_object.flushOutput()

		_object.write('outlevel 1\r\n')
		print _object.readline().replace("\r\n", "")
		print _object.readline().replace("\r\n", "")

		_object.write('monitor\r')
		_object.readline().replace("\r", "")
		_object.readline().replace("\r", "")
		_Bheader = _object.readline().replace("\r", "")
		
		_header = _Bheader.strip().split(', ')
		_header_cor = ['hello{0}'.format(i) for i in _header]
		if _header_full == []:
			_header_full = _header_cor
		else:
			_header_full = _header_full.insert(len(_header_full),_header_cor)
		print 'Header'
		print _header
		print 'Header cor'
		print _header_cor
		print 'Header full'
		print _header_full


	# I2C_1
	_datetime_i2c_dev, _value_i2c_dev = i2cdevice_read(_I2Cdevice, 2)

	print 'I2C'
	print _datetime_i2c_dev, _value_i2c_dev

	# SHT31
	# _datetime_sht31_dev, _temp_sht31_dev, _hum_sht31_dev = sht31_read(_sht31device)
	# Then read everything
	while _object.is_open:
		_BRow = _object.readline()
		if _BRow != '':
			_fRow = _BRow.strip().split(', ')
			print _fRow	

	# Combine it all


@celery_app.task
def serial_dev_read(_serial_object):
	# _serial_object.flushInput()
	_datetime = datetime.datetime.now()
	_buffer = _serial_object.readline()
	try:
		_result = _buffer.strip().split(', ')
	except:
		pass
	return _datetime, _result

@celery_app.task
def serial_dev_write(_serial_object, _data):
	_serial_object.write(_data)

@celery_app.task
def serial_dev_close(_serial_object):
	_serial_object.close()

# I2C device Generic
@celery_app.task
def i2cdevice_init(_I2Cdevice):
	return True

@celery_app.task
def i2cdevice_read(_I2Cdevice, _packetsize):
    _datetime = datetime.datetime.now()
    _readValue = _I2Cdevice.read(_packetsize)
    return _datetime, _readValue

@celery_app.task
def i2cdevice_write(_I2Cdevice, _data):
	_ack = _I2Cdevice.write(_data)
	return _ack

#I2C device SHT31
@celery_app.task
def sht31_init(_sht31device):
	return True

@celery_app.task
def sht31_read(_sht31device):
    _datetime = datetime.datetime.now()
    _tempereature, _humidity = _sht31device.read()
    return _temperature, _humidity

