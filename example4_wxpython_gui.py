#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Example GUI in wxPython to control multiple Mesytec MHV-4 units
# connected to USB ports.
# Joonas Konki - 04/06/2018

import wx
import mhv4lib
import time
from serial.tools import list_ports

RAMP_VOLTAGE_STEP = 1
RAMP_WAIT_TIME = 1
VOLTAGE_LIMIT = 100
USING_NEW_FIRMWARE = True

class Channel:
	def __init__(self, parent, number):
		self.channel = number
		self.voltage = 0.
		self.current = 0.
		self.polarity = 0
		self.enabled = 0

class Unit:
	def __init__(self, serial, name):
		self.port = ''
		self.mhv4 = None
		self.name = name
		self.serial = serial
		self.rampspeed = 0
		self.channels = []
		for i in [0,1,2,3]:
			self.channels.append(Channel(self,i))
			
	def connect(self):
		self.mhv4 = mhv4lib.MHV4(self.port, baud=9600)
		
	def disconnect(self):
		self.mhv4.close()
		
	def updateValues(self, channel=4):
		
		if self.mhv4 is None: # FOR DEBUGGING
			print("MHV4 unit %s not found?" % self.name)
			return
			
		if channel < 4: # update values for only one channel in the unit
			self.channels[channel].voltage = self.getVoltage(channel)
			self.channels[channel].current = self.getCurrent(channel)
			self.channels[channel].enabled = 1 if self.channels[channel].voltage > 0.1 else 0
			self.channels[channel].polarity = self.getPolarity(channel)					
				
		else :	# update on all channels in the unit
			for ch in self.channels:
				ch.voltage = self.getVoltage(ch.channel)
				ch.current = self.getCurrent(ch.channel)
				if ch.voltage > 0.1 :
					self.channels[channel].enabled = 1
		
	def enableChannel(self,channel):
		if self.getVoltage(channel) > 0.1 : 
			print("Unit %s channel %d is already ON ?" % (self.name, channel) )
			return
			
		voltagePreset = 0 # Voltage to be ramped to
		if USING_NEW_FIRMWARE :
			voltagePreset = self.getVoltagePreset(channel)
			
		self.setVoltage(0)
		time.sleep(RAMP_WAIT_TIME)
		self.mhv4.set_on(channel)
		time.sleep(RAMP_WAIT_TIME)		
		self.setVoltage(voltagePreset)
	
	def disableChannel(self,channel):
		curvoltage = self.getVoltage(channel)	
		while curvoltage > 0.1:
			self.mhv4.set_voltage(channel, max( 0, int(curvoltage)-RAMP_VOLTAGE_STEP ))
			time.sleep(RAMP_WAIT_TIME)
			curvoltage = self.getVoltage(channel)
			self.updateValues(channel)			

		self.mhv4.set_off(channel)
		time.sleep(RAMP_WAIT_TIME)
		self.channels[channel].enabled = 0
		self.updateValues(channel)
	
	def setPolarity(self,channel,pol):
		curvoltage = self.getVoltage(channel)
		if curvoltage < 0.1:
			self.mhv4.set_voltage_polarity(channel,pol)
			self.channels[channel].polarity = int(pol)
		else:
			print("Channel " + str(channel) + " is ON. Turn it off first.")

	def getPolarity(self, channel):
		pol =  self.mhv4.get_voltage_polarity(channel)
		self.channels[channel].polarity = int(pol)
		return pol		
	
	def setVoltage(self,channel,voltage):
		if voltage > VOLTAGE_LIMIT: 
			print("Set voltage too high (limit is " + str(VOLTAGE_LIMIT) + " V).")
			return
		
		# Ramp voltage slowly up or down
		curvoltage = self.getVoltage(channel)		
		while abs(voltage - curvoltage) > RAMP_VOLTAGE_STEP:
			newvoltage = curvoltage
			if (voltage - curvoltage > 0) : newvoltage = int(curvoltage)+RAMP_VOLTAGE_STEP # going up
			else : newvoltage = int(curvoltage)-RAMP_VOLTAGE_STEP # coming down
			self.mhv4.set_voltage(channel, newvoltage)
			time.sleep(RAMP_WAIT_TIME) # wait time before taking the next voltage step
			curvoltage = self.getvoltage(channel)
			self.updateValues(channel)
		
		# Finally after ramping, set the final requested value
		self.mhv4.set_voltage(channel, voltage)
		time.sleep(RAMP_WAIT_TIME)
		self.updateValues(channel)		

	def getVoltage(self,channel):
		return abs(self.mhv4.get_voltage(channel))
		
	def getVoltagePreset(self,channel): # Not in old firmware !
		return self.mhv4.get_voltage_preset(channel)
		
	def getCurrent(self,channel):
		return self.mhv4.get_current(channel)
			
class ChannelView(wx.StaticBox):
	def __init__(self,parent,number):
		wx.StaticBox.__init__(self, parent,number,"HV"+str(number),size=(220,160))
		self.number = number
		self.unit = parent
		
		#self.voltageBox1 = wx.StaticBox(self, -1, "HV"+str(number), size=(220,180))
		self.bsizer1 = wx.GridBagSizer()
		self.voltageLabel = wx.StaticText(self, -1, "Voltage (V):")
		self.currentLabel = wx.StaticText(self, -1, "Current (uA):")
		self.voltageValue = wx.TextCtrl(self, -1, "0.0", size=(100, -1), style=wx.ALIGN_RIGHT|wx.TE_READONLY)
		self.currentValue = wx.TextCtrl(self, -1, "0.0", size=(100, -1), style=wx.ALIGN_RIGHT|wx.TE_READONLY)
		self.setVoltageValue = wx.TextCtrl(self, -1, "0", size=(100, -1), style=wx.ALIGN_RIGHT)
		self.setVoltageButton = wx.Button(self, number, "SET", (20, 80))
		self.Bind(wx.EVT_BUTTON, self.OnClickSetVoltageButton, self.setVoltageButton)
		
		self.polList = ['+', '-']
		self.polSizer = wx.BoxSizer(wx.VERTICAL)
		self.polrb = wx.RadioBox(
				self, -1, "Polarity", wx.DefaultPosition, wx.DefaultSize,
				self.polList, 2, wx.RA_SPECIFY_COLS
				)
		self.polrb.SetToolTip(wx.ToolTip("Select voltage polarity (+ or -)"))		
		self.Bind(wx.EVT_RADIOBOX, self.EvtPolarityRadioBox, self.polrb)
		
		self.enableList = ['ON', 'OFF']
		self.enableSizer = wx.BoxSizer(wx.VERTICAL)
		self.enablerb = wx.RadioBox(
				self, -1, "Enable channel", wx.DefaultPosition, wx.DefaultSize,
				self.enableList, 2, wx.RA_SPECIFY_COLS
				)
		self.enablerb.SetToolTip(wx.ToolTip("Set channel ON or OFF"))		
		self.Bind(wx.EVT_RADIOBOX, self.EvtEnableRadioBox, self.enablerb)
		
		self.bsizer1.Add(self.voltageLabel, (0,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.voltageValue, (0,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.currentLabel, (1,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.currentValue, (1,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.setVoltageValue, (2,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.setVoltageButton, (2,2), flag=wx.EXPAND )
		self.bsizer1.Add(self.polrb, (3,1), flag=wx.EXPAND )
		self.bsizer1.Add(self.enablerb, (3,2), flag=wx.EXPAND )
		
		self.SetSizer(self.bsizer1)
		
		self.unit.mhv4unit.updateValues() # Get initial values from the unit
		self.updateValues()               # Update GUI with the initial values
		
	def updateValues(self):
		curvoltage = self.unit.mhv4unit.channels[self.number].voltage
		curcurrent = self.unit.mhv4unit.channels[self.number].current
		curpolarity = self.unit.mhv4unit.channels[self.number].polarity
		curenable = self.unit.mhv4unit.channels[self.number].enabled
		curpolaritysel = 1 if (curpolarity == 0) else 0	# invert the selection that comes from the RadioBox !
		curenablesel   = 1 if (curenable == 0)   else 0 # invert the selection that comes from the RadioBox !
		if curenable == 1 : 
			self.enablerb.SetForegroundColour('#ff0000')
			self.polrb.Enable(False)
		else : 
			self.enablerb.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
			self.polrb.Enable(True)
		
		self.voltageValue.SetValue(str(curvoltage))
		self.currentValue.SetValue(str(curcurrent))
		self.polrb.SetSelection(curpolaritysel)
		self.enablerb.SetSelection(curenablesel)
		
	def OnClickSetVoltageButton(self, event):
		newvoltage = float( self.setVoltageValue.GetValue() )
		print("Set voltage of unit %s channel %d to %.2f" % (self.unit.mhv4unit.name, self.number, newvoltage) )
		self.unit.mhv4unit.channels[self.number].voltage = newvoltage
		self.updateValues()
		
	def EvtPolarityRadioBox(self, event):
		if self.unit.mhv4unit.channels[self.number].enabled == 1 or self.unit.mhv4unit.channels[self.number].voltage > 0.1 :
			print("Unit %s Channel %d is ON. Turn it off first." % (self.unit.mhv4unit.name, self.number) )
			selection = 1 if (self.unit.mhv4unit.channels[self.number].polarity == 0) else 0
			self.polrb.SetSelection(selection)
			return
		
		selection = self.polrb.GetSelection()
		newpolarity = 1 if (selection == 0) else 0 # invert the selection that comes from the RadioBox !
		print("Set polarity of unit %s channel %d to %d" % (self.unit.mhv4unit.name, self.number, newpolarity) )
		#self.unit.mhv4unit.setPolarity(self.number,newpolarity)
		self.updateValues()
		
	def EvtEnableRadioBox(self, event):
		selection = self.enablerb.GetSelection()
		newvalue = 1 if (selection == 0) else 0 # invert the selection that comes from the RadioBox !
		print("Set enable of unit %s channel %d to %d" % (self.unit.mhv4unit.name, self.number, newvalue) )
		
		if 1 == newvalue :			
			self.unit.mhv4unit.enableChannel(self.number)
		if 0 == newvalue : 
			self.unit.mhv4unit.disableChannel(self.number)
			
		
		self.unit.mhv4unit.channels[self.number].enabled = newvalue

		self.updateValues()

class UnitView(wx.Panel):	
	"""
	Class that displays all of the channels of one unit in one wx.Panel
	"""
   
	def __init__(self,parent, mhv4unit):
		wx.Panel.__init__(self, parent, size=(250,-1))
		self.mhv4unit = mhv4unit
		
		#self.SetBackgroundColour('#ededed') # Normal gray
		self.SetBackgroundColour('#f0f000') # Mesytec yellow
		self.unitNameLabel = wx.StaticText(self, label=self.mhv4unit.name)
		self.mhvPanSizer = wx.GridBagSizer()		
		self.mhvPanSizer.Add(self.unitNameLabel, (0, 0), span=(0,2), flag=wx.ALIGN_CENTER)
		
		self.channelViews = []
		
		for i in range(4):
			self.channelViews.append(ChannelView(self,i))
			self.mhvPanSizer.Add(self.channelViews[i], (2+i, 1))
			
		self.SetSizer(self.mhvPanSizer)
	

class MHV4GUI(wx.Frame):

	def __init__(self, parent, mytitle, mymhv4units):
	
		self.mhv4units = mymhv4units
		width = 270+270*(abs(len(mymhv4units)-1))
		super(MHV4GUI, self).__init__(parent, title=mytitle,size=(width,740))

		self.InitUI()
		self.Centre()

	def InitUI(self):

		panel = wx.Panel(self)
		panel.SetBackgroundColour('#4f5049')
		vbox = wx.BoxSizer(wx.HORIZONTAL)
		
		for unit in self.mhv4units: # Create a view for each MHV4 unit
			vbox.Add(UnitView(panel, unit), wx.ID_ANY, wx.EXPAND | wx.ALL, 5)

		panel.SetSizer(vbox)


def main():

	mhv4units = []
	mhv4units.append(Unit('0318132','Recoil dE'))
	mhv4units.append(Unit('0318131','Recoil E' ))
	mhv4units.append(Unit('0318134','Stub'))
	mhv4units.append(Unit('0318133','dE-E'))
	
	print('Looking up ports for the MHV4 units in (/dev/tty*) ...')
	ports = list_ports.comports()
	foundmhv4units = []
	for unit in mhv4units:
		for port in ports:
			if port.serial_number == unit.serial:
				unit.port = port.device
				print("Found MHV-4 unit (" + str(unit.serial) + "," + str(unit.name) + ") in port: " + str(unit.port) )
				break
		if unit.port == '':
			print("MHV-4 unit (" + str(unit.serial) + "," + str(unit.name) + ") was not found.")	
			foundmhv4units.append(unit)		
		else :
			foundmhv4units.append(unit)
			unit.connect()

	app = wx.App()
	gui = MHV4GUI(None, 'MHV4GUI', foundmhv4units)
	gui.Show()
	app.MainLoop()


if __name__ == '__main__':
	main()
	
