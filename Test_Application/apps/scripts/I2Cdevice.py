#~ I2C functions
# import smbus
import time

class I2Cdevice(object):

	def __init__(self, address = 0x00, packetSize = 2, pollspeed = 0.1):
		self.address = address
		self.packetSize = packetSize
		self.pollspeed = pollspeed
		# self.bus = smbus.SMBus(1)
		self.run = False

	def start(self):
		self.run = True
		t1 = threading.Thread(target=self.readLoop)
		t1.start()

	def stop(self):
		self.run = False

	def readLoop(self):
		while self.run:
			self.read(2)

	def check(self):
		return self.run

	def read(self, pack):

		# i = 0
		# _value = 0
		
		# while (i < self.packetSize):

		# 	_measure = self.bus.read_i2c_block_data(self._address, 0, 1)
		# 	_value |= _measure[0] << (8*(self.packetSize-(1+i)))
		# 	i+=1
		_value = 10
		return _value

	def write(self, message):
		# self.bus.write_i2c_block_data(self.address,0,[message])
		print 'written ' + str(message) + ' to ' + str(self.address) + ' address'