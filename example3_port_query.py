#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Example script to query for the serial number of the Mesytec MHV-4 unit
# that is connected to the USB port
# Joonas Konki - 25/05/2018

import mhv4lib
import time
from serial.tools import list_ports

myport = ''
mhv4serialno = '0914067'
ports = list_ports.comports()
for port in ports:
	if port.serial_number == mhv4serialno:
		myport = port.device
		print("Found MHV-4 unit (" + str(mhv4serialno) + ") in port: " + str(port.device) )
		break

# MHV4 unit not found
if myport == '':
	print("MHV4 unit is not connected, exiting...")
	exit()

mymhv4 = mhv4lib.MHV4(myport, baud=9600)

val = mymhv4.get_ramp()
print("MHV-4 ramp speed is: " + str(val) + " V/s")

mymhv4.close()
