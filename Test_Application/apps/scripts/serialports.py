import sys, glob, serial

def serialports():
	"""Lists serial ports

	:raises EnvironmentError:
		On unsupported or unknown platforms
	:returns:
		A list of available serial ports
	"""
	if sys.platform.startswith('win'):
		ports = ['COM' + str(i + 1) for i in range(256)]

	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		# this is to exclude your current terminal "/dev/tty"
		ports = glob.glob('/dev/tty[A-Za-z]*')

	elif sys.platform.startswith('darwin'):
		ports = glob.glob('/dev/tty.*')

	else:
		raise EnvironmentError('Unsupported platform')

	result = []

	for port in ports:
		try:
			s = serial.Serial(port)
			s.close()
			if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
				if 'tty' in port:
					result.append(port)
			elif sys.platform.startswith('darwin'):
				if 'usb' in port:
					result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result