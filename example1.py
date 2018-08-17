#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Example script to set and read voltages from a Mesytec MHV-4 unit
# using the USB port for serial communication
# Joonas Konki - 25/05/2018

import mhv4lib
import time

mymhv4 = mhv4lib.MHV4('/dev/ttyUSB0', baud=9600)


val = mymhv4.get_ramp()
print("MHV-4 ramp speed is: " + str(val) + " V/s")

# Set first channel voltage to zero
mymhv4.set_voltage(0,0)
time.sleep(2)
val = mymhv4.get_voltage_preset(0)
print("Channel 0 voltage set to: " + str(val) + " V")

# Set first channel voltage to 1.0 V
mymhv4.set_voltage(0,1)
time.sleep(2)
val = mymhv4.get_voltage_preset(0)
print("Channel 0 voltage set to: " + str(val) + " V")

# Turn the voltage ON for the first channel
mymhv4.set_on(0)
time.sleep(2)

val = mymhv4.get_voltage(0)
print("Channel 0 voltage reading is after ON: " + str(val) + " V")

val = mymhv4.get_current(0)
print("Channel 0 current is after ON: " + str(val) + " uA")

# Turn the voltage OFF for the first channel
mymhv4.set_off(0)
time.sleep(2)
val = mymhv4.get_voltage(0)
print("Channel 0 voltage is after OFF " + str(val) + " V")

mymhv4.set_voltage(0, 0)
val = mymhv4.get_voltage_preset(0)
print("Channel 0 voltage set to: " + str(val) + " uA")

mymhv4.close()
