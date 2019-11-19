#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arjan de Haan (Vepnar)
import re
import sys
from . import processor, logger
from subprocess import Popen, PIPE
from datetime import datetime

def enable():
    # Recieve config settings and format the command
    interface = processor.config.get('NETWORK','interface')
    command = f'ifconfig {interface}'

    # Execute the command and recieve the output
    pipe = Popen(command, shell=True, stdout=PIPE)
    command_output = pipe.communicate()[0].decode("ascii")
    
    # Check if there are any errors found the the terminal output
    if ' error ' in command_output:
        logger.err("Interface is not found")
        sys.exit(1)
        
    logger.debug('Interface loaded')

def receive_values():
    interface = processor.config.get('NETWORK','interface')   
    command = f'ifconfig {interface}'

    # Open subprocess and parse output
    pipe = Popen(command, shell=True, stdout=PIPE)
    command_output = pipe.communicate()[0].decode("ascii")

    # Find byte values with regex
    parser_regex = r'bytes ([0-9]*)'
    values = re.findall(parser_regex, command_output)

    try:
        # Convert to int
        return int(values[0]), int(values[1])
    except:
        # Logger potential error to he console and return 0,0
        logger.err('Couldn\'t recieve data on the interface')
        return 0, 0

def check_disabletrigger(total):
    # Only execute when this function is enabled
    if not processor.config.getboolean('NETWORK', 'disabletrigger'):
        return

    # Recieve threshhold and command from the config file
    threshold = processor.config.getint('NETWORK', 'disablethreshold')
    command = processor.config.get('NETWORK','disablecommand')

    # Check if the threshold total values is higher than the threshold
    if total > threshold:
        logger.log('The interface passed the second threshold and the command is executed')

        # Execute command insert into the config file
        pipe = Popen(command, shell=True, stdout=PIPE)
        processor.config.set('NETWORK','disabletrigger','False')

# Make the large numbers more readable
def byte_formatter(value):
    # Could add more options here but only in the power of 3
    byte_units = ['B ', 'kB', 'MB', 'GB', 'TB']
    options = len(byte_units)
    size = len(str(value))

    for i in reversed(range(options)):
        if value >= 1000 ** i:
            # Shrink values and return them
            reduced = value / 1000 ** i
            return reduced , byte_units[i]
    return value, byte_units[0]

def print_usage(rx, tx):
    # Calculate and process values
    rx_int, rx_unit = byte_formatter(rx)
    tx_int, tx_unit = byte_formatter(tx)
    tt_int, tt_unit = byte_formatter(rx+tx)

    # format the information and print it to the console
    message = f'Recieved: {rx_int:6.2F}{rx_unit} | Send: {tx_int:6.2F}{tx_unit} | Total: {tt_int:6.2F}{tt_unit}'
    logger.log(message)

