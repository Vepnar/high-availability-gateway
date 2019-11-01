#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arjan de Haan (Vepnar)
import re
import sys
from . import processor, logger
from subprocess import Popen, PIPE
from datetime import datetime

def enable():
    interface = processor.config.get('NETWORK','interface')
    command = f'ifconfig {interface}'

    pipe = Popen(command, shell=True, stdout=PIPE)
    command_output = pipe.communicate()[0].decode("ascii")
    
    if ' error ' in command_output:
        logger.err("Interface is not found")
        sys.exit(1)
        
    logger.debug('Interface loaded')

def recieve_values():
    interface = processor.config.get('NETWORK','interface')   
    command = f'ifconfig {interface}'

    # Open subprocess and parse output
    pipe = Popen(command, shell=True, stdout=PIPE)
    command_output = pipe.communicate()[0].decode("ascii")

    # Find byte values
    parser_regex = r'bytes ([0-9]*)'
    values = re.findall(parser_regex, command_output)

    # Convert to int
    try:
        return int(values[0]), int(values[1])
    except:
        logger.err('Couldn\'t recieve data on the interface')
        return 0, 0

def check_disabletrigger(total):
    if not processor.config.getboolean('NETWORK', 'disabletrigger'):
        return

    threshold = processor.config.getint('NETWORK', 'disablethreshold')
    command = processor.config.get('NETWORK','disablecommand')

    if total > threshold:
        logger.log('The interface passed the second threshold and the command is executed')
        pipe = Popen(command, shell=True, stdout=PIPE)
        command_output = pipe.communicate()[0].decode("ascii")
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
    # Process infomation
    message = f'Recieved: {rx_int:6.2F}{rx_unit} | Send: {tx_int:6.2F}{tx_unit} | Total: {tt_int:6.2F}{tt_unit}'
    logger.log(message)

