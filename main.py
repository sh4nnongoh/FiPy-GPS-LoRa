import machine
import math
import network
import os
import time
import utime
import socket
import binascii
import struct
import pycom
from machine import RTC
from machine import SD
from machine import Timer
from L76GNSS import L76GNSS
from pytrack import Pytrack
from network import LoRa
# setup as a station

import gc

time.sleep(2)
gc.enable()

pycom.heartbeat(False)

# Initialize LoRa in LORAWAN mode.
lora = LoRa(mode=LoRa.LORAWAN, public=0, adr=False)
#lora = LoRa.init(mode=LoRa.LORAWAN,  tx_power=14, bandwidth=LoRa.BW_125KHZ, sf=7, preamble=8, coding_rate=LoRa.CODING_4_5, power_mode=LoRa.ALWAYS_ON, tx_iq=False, rx_iq=False, adr=False, public=False, tx_retries=1, device_class=LoRa.CLASS_A)

print("")
b = os.uname()
print("Sysname: ", b.sysname)
print("Nodename: ", b.nodename)
print("Release: ", b.release)
print("Version: ", b.version)
print("Machine: ", b.machine)
print
print("LoRa MAC: ", end="")
print(binascii.hexlify(lora.mac()).upper().decode('utf-8'))

# lora-query --node-add F60410AE A f6ea76f6ab663d80 f001020304050607 f2bfc2264f593ff087bcd596a766da2a f92e45f86a4a033eff40e3c7554689ec
# create an ABP authentication params
### DEVICE A ###
dev_addr = struct.unpack(">l", binascii.unhexlify('F60410AE'.replace(' ','')))[0] # these settings can be found from TTN
nwk_swkey = binascii.unhexlify('F2BFC2264F593FF087BCD596A766DA2A'.replace(' ','')) # 
app_swkey = binascii.unhexlify('F92E45F86A4A033EFF40E3C7554689EC'.replace(' ','')) # 


# lora-query --node-add 260410AE A 16ea76f6ab663d80 0001020304050607 12bfc2264f593ff087bcd596a766da2a e92e45f86a4a033eff40e3c7554689ec
# create an ABP authentication params
### DEVICE B ###
#dev_addr = struct.unpack(">l", binascii.unhexlify('260410AE'.replace(' ','')))[0] # these settings can be found from TTN
#nwk_swkey = binascii.unhexlify('12BFC2264F593FF087BCD596A766DA2A'.replace(' ','')) # 
#app_swkey = binascii.unhexlify('E92E45F86A4A033EFF40E3C7554689EC'.replace(' ','')) # 

# remove all the non-default channels
print('Removing Channels')
for i in range(0, 15):
	print('Removing ', i)
	lora.remove_channel(i)

# set the 3 default channels to the same frequency
print('Adding Channel')
### DEVICE A ###
lora.add_channel(0, frequency=923200000, dr_min=0, dr_max=5)
lora.add_channel(1, frequency=923200000, dr_min=0, dr_max=5)
lora.add_channel(2, frequency=923200000, dr_min=0, dr_max=5)
### DEVICE B ###
#lora.add_channel(0, frequency=923400000, dr_min=0, dr_max=5)
#lora.add_channel(1, frequency=923400000, dr_min=0, dr_max=5)
#lora.add_channel(2, frequency=923400000, dr_min=0, dr_max=5)


print('Joining...')
lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))
print('Joined.')
# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 2)
#s.setsockopt(socket.SOL_LORA, socket.SO_CONFIRMED, False)
# make the socket blocking
s.setblocking(True)
s.settimeout(5)

print('Setting up GPS...')
# setup rtc
rtc = machine.RTC()
rtc.ntp_sync("pool.ntp.org")
utime.sleep_ms(750)
print('\nRTC Set from NTP to UTC:', rtc.now())
utime.timezone(7200)
print('Adjusted from UTC to EST timezone', utime.localtime(), '\n')
py = Pytrack()
l76 = L76GNSS(py, timeout=10)
chrono = Timer.Chrono()
chrono.start()
#sd = SD()
#os.mount(sd, '/sd')
#f = open('/sd/gps-record.txt', 'w')

print('Transmitting...')
i = 1
while (True):
    pycom.rgbled(0x7f0000) # red
    coord = l76.coordinates()
    if coord[0] != "None" and coord[1] != "None":
        pycom.rgbled(0xff00) # green

    ### Device A ###
    msg = ("{},{},{}\n".format("A",coord[0],coord[1]))
    ### Device B ###
    #msg = ("{},{},{}\n".format("B",coord[0],coord[1]))

    print(msg)

    pycom.rgbled(0x7f7f00) # yellow
    s.send(msg)
    i = (i % 65536) + 1    
    time.sleep(1)
