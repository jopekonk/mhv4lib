#!/usr/bin/env python3

# Script to scan leakage currents of the MINIBALL CD detector quadrants 
# as a function of the voltage.
# Joonas Konki - 25/05/2018

import mhv4lib
import time
import numpy as np

def log(text):
	print(text)

mymhv4 = mhv4lib.MHV4('/dev/ttyUSB0', baud=9600)

scan_voltages = np.arange(0.5, 30.5, 0.5) # 0.5 V up to 30.0 V in 0.5 V steps

channels = [0,1,2,3]

res = np.zeros( ( len(scan_voltages), (len(channels)+1) ) )
i = 0
for volt in scan_voltages:	
	res[i][0] = volt
	i = i+1
	
# START SCANNING 
log('Preparing to start the scan...\n')

# Set all channels to OFF and zero voltage
log('Setting voltages to zero\n')
for ch in channels:
	mymhv4.set_off(ch)
	mymhv4.set_voltage(ch, 0)

log('Voltages set to zero. Turning all channels ON\n')	
time.sleep(3)
for ch in channels:
	mymhv4.set_on(ch)

log('Channels turned ON.\n')	
time.sleep(3)

log('Start scanning voltages.\n')		
i=0	
for volt in scan_voltages:
	log('Scanning voltage: ' + str(volt))

	for ch in channels:
		mymhv4.set_voltage(ch, volt)
		
	time.sleep(10) # wait for voltages to ramp up before reading the current

	for ch in channels:
		cur = mymhv4.get_current(ch)		
		res[i][ch+1] = mymhv4.get_current(ch)
		if cur > 1.:  # safety check
			print("CURRENT LIMIT REACHED! STOPPING !!!!")
			exit()

	i = i+1

log('Stop scanning...\n')
log('Setting voltages to zero\n')
for ch in channels: # Ramp all channels to OFF, zero voltage
	curvoltage = mymhv4.get_voltage(ch)
	print("ch " + str(ch) + " curvoltage " + str(curvoltage))
	while abs(curvoltage) > 0:
		mymhv4.set_voltage(ch, int(abs(curvoltage))-1)
		time.sleep(5)
		curvoltage = mymhv4.get_voltage(ch)
		
	mymhv4.set_off(ch)
	

mymhv4.close()

np.savetxt("output.txt", res, fmt='%.3f', delimiter=' ')

