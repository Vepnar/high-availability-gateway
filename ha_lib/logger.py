#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Arjan de Haan (Vepnar)

from colorama import Fore, Style
from datetime import datetime
from . import processor

def default(msg, level, icon):

    # Recieve time and format it
    now = datetime.now()
    time = now.strftime('%H:%M:%S')
    date = now.strftime('%d %B %Y %H:%M:%S')

    # Log in the terminal when it is allowed
    if processor.config.getint('LOGGING', 'level') >= level and processor.config.getboolean('LOGGING','enabled'):
        message = f'{time} {Style.BRIGHT}{icon}{Style.RESET_ALL}: {msg}'
        print(message)

    #TODO add file logging

# Log level 4 (debug)
def debug(msg):
    default(msg, 4, Fore.BLUE + 'Debug')

# Log leven 3 (Info)
def log(msg):
    default(msg, 3, Fore.GREEN +'Info ')

# Log level 2 (Warning)
def warn(msg):
    default(msg, 2, Fore.YELLOW + 'Warn ')

# Log level 1 (Error)
def err(msg):
    default(msg, 1, Fore.RED + 'Error')

if __name__ == '__main__':
    debug('Test debug')
    log('Test Log')
    warn('Test warn')
    err('Test err')
