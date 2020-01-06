#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Access interface, format text and handle the threshold
Author: Arjan de Haan (Vepnar)
TODO: add async functionalty.
"""
import re
import sys
import asyncio
from subprocess import Popen, PIPE


class Interface:
    """Access the interface.

    Args:
        interface_name: (str)
        logger: (logger class)
        exit_on_crash: (boolean)
        disable_trigger: (boolean)
        disable_threshold: (int) in bytes
        disable_command: (str) in bash
        disable_timer: (int) in seconds
    """
    def __init__(self, interface_name, logger, debugging=False, disable_trigger=False,
                 disable_threshold=0, disable_command='', disable_timer=0):
        self.interface_name = interface_name
        self.logger = logger
        self.disable_trigger = disable_trigger
        self.debugging = debugging
        if disable_trigger:
            self.disable_threshold = disable_threshold
            self.disable_command = disable_command
            self.disable_timer = disable_timer

        command = f'ifconfig {self.interface_name}'
        pipe = Popen(command, shell=True, stdout=PIPE)
        command_output = pipe.communicate()[0].decode("ascii")

        # Check if there are any errors found the the terminal output
        if ' error ' in command_output:
            if self.debugging:
                raise Exception('Interface not found')
            logger.err("Interface is not found")
            sys.exit(1)
        logger.debug('Interface loaded')

    def receive_values(self):
        """Receive rx and tx values from the interface"""
        command = f'ifconfig {self.interface_name}'

        pipe = Popen(command, shell=True, stdout=PIPE)
        command_output = pipe.communicate()[0].decode("ascii")
        parser_regex = r'bytes ([0-9]*)'
        values = re.findall(parser_regex, command_output)

        try:
            return int(values[0]), int(values[1])
        except ValueError:
            self.logger.err('Couldn\'t receive data on the interface')
            return 0, 0

    def print_usage(self, received, send):
        """Format values to a beautiful string

        Args:
            received: (int) amount of bytes
            send: (int) amount of bytes
        """
        rx_int, rx_unit = byte_formatter(received)
        tx_int, tx_unit = byte_formatter(send)
        tt_int, tt_unit = byte_formatter(received + send)

        # format the information and print it to the console
        message = f'Recieved: {rx_int:6.2F}{rx_unit} | Send: {tx_int:6.2F}{tx_unit}' \
            f' | Total: {tt_int:6.2F}{tt_unit}'
        self.logger.log(message)


    async def loop(self):
        """TODO"""
        if not self.disable_trigger:
            return
        while True:
            if not self.disable_trigger:
                break
            await asyncio.sleep(self.disable_timer)
            self.check_disable_trigger(0)


    def check_disable_trigger(self, total):
        """Check if we reached our threshold.

        Args:
            total: total amount of internet usage received + send
        Return: return true if the command is executed
        """
        if total > self.disable_threshold:
            self.logger.log(
                'The interface passed the second threshold and the command is executed')

            # Execute command insert into the config file
            Popen(self.disable_command, shell=True, stdout=PIPE)
            self.disable_threshold = False
            return True
        return False

def byte_formatter(value):
    """Format bytes into a string.

    Args:
        value: (int) amount of bytes
    Return:
        value: (float) amount of bytes shrinked
        unit: (str) for example B or kB
    """
    # Could add more options here but only in the power of 3
    byte_units = ['B ', 'kB', 'MB', 'GB', 'TB']
    options = len(byte_units)
    for i in reversed(range(options)):
        if value >= 1000 ** i:
            # Shrink values and return them
            reduced = value / 1000 ** i
            return reduced, byte_units[i]
    return value, byte_units[0]
