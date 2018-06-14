# -*- coding: utf-8 -*-

"""
The library for controlling the Mesytec MHV-4 high voltage unit via
the USB serial control interface.

Protocol data format is 9600 baud 8N1 (8 bit, no parity, 1 stop bit)
The input characters are echoed before the response from the unit.
"""
__author__ = "Joonas Konki"
__license__ = "MIT, see LICENSE for more details"
__copyright__ = "2018 Joonas Konki"

import serial
import time
import re

class MHV4():
	def __init__(self,port,baud):
		self.port = port
		self.ser = serial.Serial( port=self.port, baudrate=baud, timeout=1 )
		
	def close(self):
		"""The function closes and releases the serial port connection attached to the unit. 

		"""
		self.ser.close()
			
	def set_on(self,channel):
		"""The function turns the voltage ON for the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that is to be turned ON.
		"""
		
		if channel not in [0,1,2,3,4]: return
		
		self.ser.write(b'ON %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()

	def set_off(self,channel):
		"""The function turns the voltage OFF for the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that is to be turned OFF.
		"""
		
		if channel not in [0,1,2,3,4]: return
		
		self.ser.write(b'OFF %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		self.ser.readline()

	def get_voltage(self,channel):
		"""The function returns the measured voltage reading of the given ``channel`` number. 
		The possible channel numbers are 0,1,2,3. 
		Number 4 applies to ALL channels (not tested?).
		
		Note: Returns always 0, if the channel is turned OFF !
		
		:param channel: The channel number of which the voltage reading is requested. 
						The return value is positive or negative depending on the set polarity.
		"""
		self.ser.write(b'RU %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline() # read echo of the command sent
		reading = self.ser.readline() # read response from the unit
		linestr = reading.decode('utf8')
		
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			voltage = float(pattern.group(2))
			if pattern.group(1) == '-':
				voltage = -voltage
			return voltage
		else :
			return 0.
			
	def get_voltage_preset(self,channel):
		"""The function returns the preset voltage reading of the given ``channel`` number.
		Note: This may not be the actual voltage, just what is set on the display.
		May not work on an older firmware of the module, and have to use get_voltage() instead. 
		The possible channel numbers are 0,1,2,3. 
		Number 4 applies to ALL channels (not tested?).
		
		:param channel: The channel number of which the preset voltage reading is requested. 
						The return value is positive regardless of what the polarity is set to.
		"""
		self.ser.write(b'RUP %d\r' % channel)
		time.sleep(0.1)
		line1 = self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			voltage = float(pattern.group(2))
			if pattern.group(1) == '-':
				voltage = -voltage
			return voltage
		else :
			return 0.
			
	def get_current(self,channel):
		self.ser.write(b'RI %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			current = float(pattern.group(2))
			if pattern.group(1) == '-':
				current = -current
			return current
		else :
			return 0.
			
	def get_current_limit(self,channel):
		""" not tested !"""
		self.ser.write(b'RIL %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		
		pattern = re.match(r'.*([+-])(\d*.\d*)', linestr, re.IGNORECASE)
		
		if pattern is not None:
			current = float(pattern.group(2))
			if pattern.group(1) == '-':
				current = -current
			return current
		else :
			return 0.
			
	def get_polarity(self,channel):
		""" not tested !"""
		self.ser.write(b'RP %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		return linestr
		
	def get_temp(self,inputc):
		""" not tested ! Get temperature at given input"""
		self.ser.write(b'RT %d\r' % inputc)
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		return linestr
	
	def get_temp_comp(self,channel):
		""" not tested ! Get complete settings for temperature compensation of 
		given channel"""
		self.ser.write(b'RTC %d\r' % channel)
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')
		return linestr
			
	def get_ramp(self):
		self.ser.write(b'RRA\r')
		time.sleep(0.1)
		self.ser.readline()
		reading = self.ser.readline()
		linestr = reading.decode('utf8')		
		pattern = re.match(r'.*:.?(\d*).*V.*', linestr, re.IGNORECASE)		
		if pattern is not None:
			ramp = float(pattern.group(1))
			return ramp
		else :
			return -1
		
		
	def set_voltage(self,channel, voltage):
		"""The function sets the voltage of the given ``channel`` number to ``voltage``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the voltage setting is applied to.
		:param voltage: The voltage that is to be set for the channel in Volts.
		"""
		if voltage > 50.:
			return
		
		self.ser.write(b'SU %d %d\r' % (channel, voltage*10)) # in 0.1 V units
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()
		
	def set_current_limit(self,channel, limit):
		"""The function sets the current limit of the given ``channel`` number 
		to ``limit``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the current limit setting is applied to.
		:param limit: The current limit value that is to be set for the channel in units of nA.
		"""

		self.ser.write(b'SIL %d %d\r' % (channel, limit)) # in nano amps for Mesytec
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()
		
	def set_voltage_limit(self,channel, limit):
		"""The function sets the voltage limit of the given ``channel`` number 
		to ``limit``. 
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		:param channel: The channel number that the voltage limit setting is applied to.
		:param limit: The voltage limit value that is to be set for the channel in units of Volts.
		"""
		self.ser.write(b'SUL %d %d\r' % (channel, limit*10)) # given in units of 0.1 V for Mesytec
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()
		
	def set_voltage_polarity(self,channel, pol):
		"""The function sets the voltage polarity (negative/positive) for the given ``channel`` number.
		The possible channel numbers are 0,1,2,3. Number 4 applies to ALL channels.
		
		Note:   SP c p , 
				where c = channel, p = polarity: p/+/1 or n/-/0 
				e.g.: SP 0 n sets the polarity of channel 0 to negative.
		    	
				For security reasons: if HV is on, it will be switched off automatically, 
				HV preset will be set to 0 V, polarity is switched when	HV is down.
				
				After switching: set presets again to desired values.
				
		:param channel: The channel number that the polarity change is applied to.
		:param pol: The desired polarity of the voltage for the channel 0 or 1.
		"""
		self.ser.write(b'SP %d %d\r' % (channel, pol))
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()
		
	def set_ramp(self, n):
		"""The function sets the HV ramp speed of the whole unit.
		
		Note:   Options are:
		        n = 0: 5 V/s, 1: 25 V/s, 2: 100 V/s, 3: 500 V/s
								
		:param n: The desired ramp speed option (0, 1, 2 or 3).
		"""
		
		if n not in [0,1,2,3]: return
		
		self.ser.write(b'SRA %d\r' % (n))
		time.sleep(0.1)
		self.ser.readline()
		response = self.ser.readline()
		
