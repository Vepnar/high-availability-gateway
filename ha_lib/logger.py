#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contains class to log information to a file or to the terminal.
Author: Arjan de Haan (Vepnar),
Last edited: 6 January 2020
"""

from datetime import datetime
from colorama import Fore, Style

class Logger:
    """Log information to terminal or file.

    Args:
        logging_level: (1-4)
        terminal_logging: (boolean)
        file_logging: (boolean)
        logging_file: (str) string to path it should log to. can be None
    """

    def __init__(self, logging_level, terminal_logging, file_logging, logging_file=None):
        self.logging_level = logging_level
        self.terminal_logging = terminal_logging
        self.file_logging = file_logging

        if logging_file is None and file_logging:
            terminal_logging = False
            self.err('Logging file not set')
        if file_logging:
            self.logging_file = open(logging_file, 'a')

    def default(self, msg, level, icon):
        """Format information into a beautiful message.

        Args:
            msg: String of message to print.
            level: level to of the message.
            icon: special icon of the message usually a colour with some word.
        """

        now = datetime.now()
        time = now.strftime('%H:%M:%S')
        date = now.strftime('%d %B %Y %H:%M:%S')

        # Log in the terminal when it is allowed
        if self.logging_level >= level and self.terminal_logging:
            message = f'{time} {Style.BRIGHT}{icon}{Style.RESET_ALL}: {msg}'
            print(message)

        if self.logging_level >= level and self.file_logging:
            message = f'[{date}][{level}]# {msg}\n'
            self.logging_file.write(message)
            self.logging_file.flush()


    # Log level 4 (debug)
    def debug(self, msg):
        """Print debug message"""
        self.default(msg, 4, Fore.BLUE + 'Debug')

    # Log level 3 (Info)
    def log(self, msg):
        """Print log message"""
        self.default(msg, 3, Fore.GREEN +'Info')

    # Log level 2 (Warning)
    def warn(self, msg):
        """Print warning message"""
        self.default(msg, 2, Fore.YELLOW + 'Warn')

    # Log level 1 (Error)
    def err(self, msg):
        """Print error message"""
        self.default(msg, 1, Fore.RED + 'Error')

    def __del__(self):
        """Close logging file"""
        if self.file_logging:
            try:
                self.logging_file.close()
            except:
                pass
