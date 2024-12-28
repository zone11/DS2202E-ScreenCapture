#!/usr/bin/env python3

from telnetlib_receive_all import Telnet
import time
from PIL import Image
import io
import sys
import os
import platform
import logging

__version__ = 'v0.2'
# 0.1 Mod for DS2202E by zone11
# 0.2 Python3 compatibility by doug-a-brunner and cleanup/removals by zone11

__author__ = 'zone11, doug-a-brunner, RoGeorge'

# Set the desired logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=os.path.basename(sys.argv[0]) + '.log',
                    filemode='w')

logging.info("***** New run started...")
logging.info("OS Platform: " + str(platform.uname()))
logging.info("Python version: " + str(sys.version) + ", " + str(sys.version_info))


# Update the next lines for your own default settings:
path_to_save = "captures/"
DEFAULT_FORMAT = "png"
DEFAULT_IP = "192.168.44.174"

# Rigol/LXI specific constants
port = 5555
big_wait = 10
smallWait = 1
company = 0
model = 1
serial = 2

# Send operational command to the device
def command(tn, scpi):
    logging.info("SCPI to be sent: " + scpi)
    answer_wait_s = 1
    response = ""
    while response != "1\n":
        tn.write(b"*OPC?\n")  # previous operation(s) has completed ?
        logging.info("Send SCPI: *OPC? # May I send a command? 1==yes")
        response = tn.read_until(b"\n", 1).decode()  # wait max 1s for an answer
        logging.info("Received response: " + response)

    tn.write(scpi.encode() + b"\n")
    logging.info("Sent SCPI: " + scpi)
    response = tn.read_until(b"\n", answer_wait_s).decode()
    logging.info("Received response: " + response)
    return response

# Send bit command to the device
def command_bin(tn, scpi):
    logging.info("SCPI to be sent: " + scpi)
    answer_wait_s = 1
    response = b""
    while response != b"1\n":
        tn.write(b"*OPC?\n")  # previous operation(s) has completed ?
        logging.info("Send SCPI: *OPC? # May I send a command? 1==yes")
        response = tn.read_until(b"\n", 1)  # wait max 1s for an answer
        logging.info("Received response: " + repr(response))

    tn.write(scpi.encode() + b"\n")
    logging.info("Sent SCPI: " + scpi)
    response = tn.read_until(b"\n", answer_wait_s)
    logging.info("Received response: " + repr(response))
    return response

# decode header bytes
def tmc_header_bytes(buff):
    return 2 + int(buff[1:2].decode())


def expected_data_bytes(buff):
    return int(buff[2:tmc_header_bytes(buff)].decode())


def expected_buff_bytes(buff):
    return tmc_header_bytes(buff) + expected_data_bytes(buff) + 1
    
# print script usage    
def print_help():
    print()
    print("Usage:")
    print("    " + "python3 " + script_name + " png|bmp [oscilloscope_IP [save_path]]")
    print()
    print("Usage examples:")
    print("    " + "python3 " + script_name + " png")
    print("    " + "python3 " + script_name + " png 192.168.1.3")
    print()
    print("This program captures captures whatever is displayed on the screen of a Rigol DS2202E series oscilloscope as an image")
    print("The program is using LXI protocol, so the computer must have LAN connection with the oscilloscope.")
    print("USB and/or GPIB connections are not used by this software.")
    print()
    print("No VISA, IVI or Rigol drivers are needed.")
    print()

# Check command line parameters
script_name = os.path.basename(sys.argv[0])

# Read/verify file type
if len(sys.argv) <= 1:
    print("Warning - No command line parameters, using defaults")
elif sys.argv[1].lower() not in ["png", "bmp"]:
    print_help()
    print("This file type is not supported: ", sys.argv[1])
    sys.exit("ERROR")

# Fileformat
if len(sys.argv) > 1: 
	file_format = sys.argv[1].lower()
else:
	file_format = DEFAULT_FORMAT

# IP Address
if len(sys.argv) > 2:
    IP_RIGOL = sys.argv[2]
else:
	IP_RIGOL = DEFAULT_IP
	
# Check network response (ping)
if platform.system() == "Windows":
    response = os.system("ping -n 1 " + IP_RIGOL + " > nul")
else:
    response = os.system("ping -c 1 " + IP_RIGOL + " > /dev/null")

if response != 0:
    print
    print("WARNING! No response pinging " + IP_RIGOL)
    print("Check network cables and settings.")
    print("You should be able to ping the oscilloscope.")

# Open a modified telnet session
# The default telnetlib drops 0x00 characters, so a modified library 'telnetlib_receive_all' is used instead
# Switching to TCP Socket one day..
tn = Telnet(IP_RIGOL, port)
instrument_id = command(tn, "*IDN?")    # ask for instrument ID

# Check if instrument is set to accept LAN commands
if instrument_id == "command error":
    print("Instrument reply:", instrument_id)
    print("Check the oscilloscope settings.")
    print("Utility -> IO Setting -> RemoteIO -> LAN must be ON")
    sys.exit("ERROR")

# Check if instrument is indeed a Rigol DS2202E series
id_fields = instrument_id.split(",")

if (id_fields[company] != "RIGOL TECHNOLOGIES") or (id_fields[model] !="DS2202E"):
   print("Found instrument model", "'" + id_fields[model] + "'", "from", "'" + id_fields[company] + "'")
   print("WARNING: No Rigol DS2202E found at", IP_RIGOL)
   sys.exit('Sorry and good bye!')       

print("Instrument ID:", instrument_id)

# Prepare filename as MODEL_SERIAL_YYYY-MM-DD_HH.MM.SS
timestamp = time.strftime("%Y-%m-%d_%H.%M.%S", time.localtime())
filename = path_to_save + id_fields[model] + "_" + id_fields[serial] + "_" + timestamp


# Ask for an oscilloscope display print screen
print("Receiving screen capture...")
buff = command_bin(tn, ":DISP:DATA?")

expectedBuffLen = expected_buff_bytes(buff)
# Just in case the transfer did not complete in the expected time, read the remaining 'buff' chunks
while len(buff) < expectedBuffLen:
	logging.warning("Received LESS data then expected! (" +
					str(len(buff)) + " out of " + str(expectedBuffLen) + " expected 'buff' bytes.)")
	tmp = tn.read_until(b"\n", smallWait)
	if len(tmp) == 0:
		break
	buff += tmp
	logging.warning(str(len(tmp)) + " leftover bytes added to 'buff'.")

if len(buff) < expectedBuffLen:
	logging.error("After reading all data chunks, 'buff' is still shorter then expected! (" +
				  str(len(buff)) + " out of " + str(expectedBuffLen) + " expected 'buff' bytes.)")
	sys.exit("ERROR")

# Strip TMC Blockheader and keep only the data
tmcHeaderLen = tmc_header_bytes(buff)
expectedDataLen = expected_data_bytes(buff)
buff = buff[tmcHeaderLen: tmcHeaderLen+expectedDataLen]

# Save as PNG or BMP according to file_format
im = Image.open(io.BytesIO(buff))
im.save(filename + "." + file_format, file_format)
print("Saved file:", "'" + filename + "." + file_format + "'")

tn.close()