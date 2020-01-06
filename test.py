#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test all functions of all modules in one simple script
Author: Arjan de Haan (Vepnar),
Last edited: 6 January 2020
"""

import os
import time
from colorama import Fore, Style

TEST_FILE = './test.bin'
INTERFACE = 'wlp2s0'

def start_test_case(name):
    """Print information about the start of the test.

    Args:
        name: (str) name of the test that will start.
    """
    print(
        f'=== {Fore.MAGENTA}Starting testing: {Style.BRIGHT}{name}{Style.RESET_ALL} ===')

def progress(task, time_spent=None):
    """Print information about current progress.

    Args:
        taks: (str) name of the task that's about the be run.
        time_spent: (float) time spent since last task. Can be None when this is the first task
    Return: (float) new time for the next task.
    """
    if time_spent is not None:
        time_spent = time.time() - time_spent
        print(f'== {Fore.MAGENTA}Task: {Style.BRIGHT}{task}{Style.NORMAL}, '
              f'time spent on last task: {Style.BRIGHT}{time_spent:.3f}ms{Style.RESET_ALL} ==')
    else:
        print(f'== {Fore.MAGENTA}Task: {Style.BRIGHT}{task}{Style.RESET_ALL} ==')
    return time.time()


def end_test_case(name, time_spent, success=True):
    """Message to send when an error occurred or when the test is finished.

    Args:
        name: (str) Name of the test
        time_spent: (float) amount of time spent since the beginning of the test
        success: (bool) true when there is success
    """
    time_spent = time.time() - time_spent
    if success:
        print(f'=== {Fore.MAGENTA}Test success {Style.BRIGHT}{name}{Style.NORMAL} '
              f'time spent: {Style.BRIGHT}{time_spent:.3f}ms{Style.RESET_ALL} ===')
    else:
        print(f'=x= {Fore.MAGENTA}TEST FAILED {Style.BRIGHT}{name}{Style.NORMAL} '
              f'TIME SPENT: {Style.BRIGHT}{time_spent:.3f}ms{Style.RESET_ALL} =x=')


def easy_function_test(task, function, args, time_spent=None):
    """Test functions easily by reusing lines.

    Args:
        task: (str) name of the task
        function: (function)
        args: (dict) args of the function that should be tested
        time_spent: (float) time since beginning of function can be None when first run
    Return: (list) output of the function, new time stamp
    """
    progress(task, time_spent=time_spent)
    try:
        output = function(**args)
        return (output, time.time())
    except Exception as ex:
        if time_spent is None:
            time_spent = time.time()
        print(ex)
        end_test_case('Logger', time_spent, success=False)
        return (None, time.time())

def test_logger():
    """Testing the logger module:

    Tests:
        Init test:
            Importing module & creating object.
        Terminal message testing:
            Debug, log , warning & Error.
        File logging testing:
            Debug, log, warning & Error.
    """
    # Init test.
    start_test_case('Logger')
    time_spent = time.time()
    try:
        last_time = progress('Importing')
        from ha_lib import logger
        last_time = progress('Creating terminal testing object', last_time)
        vargs = {
            'logging_level': 4,
            'terminal_logging': True,
            'file_logging': False,
            'debug' : True
        }
        logger_object = logger.Logger(**vargs)

        # Terminal message testing.
        vargs = {'msg': 'test'}
        _, last_time = easy_function_test(
            'Debug', logger_object.debug, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Log', logger_object.log, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Warning', logger_object.warn, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Error', logger_object.err, vargs, time_spent=last_time)

        # File logging testing
        vargs = {
            'logging_level': 4,
            'terminal_logging': False,
            'file_logging': True,
            'logging_file': TEST_FILE,
            'debug' : True
        }
        if os.path.isfile(TEST_FILE):
            os.remove(TEST_FILE)

        last_time = progress(
            'Creating file testing object', time_spent=last_time)
        logger_object = logger.Logger(**vargs)
        vargs = {'msg': 'test'}
        _, last_time = easy_function_test(
            'Debug', logger_object.debug, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Log', logger_object.log, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Warning', logger_object.warn, vargs, time_spent=last_time)
        _, last_time = easy_function_test(
            'Error', logger_object.err, vargs, time_spent=last_time)

        if os.path.isfile(TEST_FILE):
            os.remove(TEST_FILE)
        end_test_case('Logging', time_spent)
    except Exception as ex:
        print(ex)
        end_test_case('Logging', time_spent, success=False)


def test_interface():
    """Testing the interface module.

    Tests:
        Importing, Creating objects, Receive values, Format bytes, Print usage, Disable trigger.
    """
    start_test_case('Interface')
    time_spent = time.time()

    try:
        last_time = progress('Importing')
        from ha_lib import interface, logger
        last_time = progress('Creating Objects', time_spent=last_time)

        # Create logger.
        vargs = {
            'logging_level': 4,
            'terminal_logging': True,
            'file_logging': False
        }
        logger_object = logger.Logger(**vargs)

        # Create Interface.
        vargs = {
            'interface_name': INTERFACE,
            'logger': logger_object,
            'debug': True,
            'disable_trigger': True,
            'disable_threshold': 1,
            'disable_command': "echo ''",
            'disable_timer': -1
        }
        interface_object = interface.Interface(**vargs)

        _, last_time = easy_function_test(
            'Receive values', interface_object.receive_values, {}, time_spent=last_time)
        _, last_time = easy_function_test(
            'Byte formatter', interface.byte_formatter,
            {'value': 10*10 ^ 16}, time_spent=last_time)
        _, last_time = easy_function_test(
            'Print usage', interface_object.print_usage,
            {'received': 54321, 'send': 12345}, time_spent=last_time)
        out, last_time = easy_function_test(
            'Disable trigger', interface_object.check_disable_trigger,
            {'total': 100}, time_spent=last_time)

        if not out:
            end_test_case('Disable trigger', last_time, success=False)
        end_test_case('Interface', time_spent)

    except Exception as ex:
        print(ex)
        end_test_case('Interface', last_time, success=False)

def test_database():
    """Test the database module.

    Tests:
        Importing, creating database, opening database, add special, add normal, get timestamp,
        get last value, check new day, check new month
    """
    start_test_case('Database')
    time_spent = time.time()
    try:
        last_time = progress('Importing')
        from ha_lib import database, logger
        last_time = progress('Creating database', time_spent=last_time)

        # Create logger.
        vargs = {
            'logging_level': 4,
            'terminal_logging': True,
            'file_logging': False,
            'debug' : True
        }
        logger_object = logger.Logger(**vargs)

        # Create database
        vargs = {
            'logger' : logger_object,
            'database_file' : TEST_FILE,
            'enabled' : True,
            'debug' : True
        }
        if os.path.isfile(TEST_FILE):
            os.remove(TEST_FILE)
        database_object = database.Database(**vargs)

        database_object, last_time = easy_function_test(
            'Reopen database', database.Database, vargs, time_spent=last_time)

        vargs = {
            'received' : 321,
            'send' : 123,
            'timestamp' : None,
            'special' : 1,
        }
        _, last_time = easy_function_test(
            'Add special', database_object.add_row, vargs, time_spent=last_time)
        vargs = {
            'received': 43,
            'send': 12,
            'timestamp': int(time.time()) - 10368000,
            'special': 0,
        }
        _, last_time = easy_function_test(
            'Add normal', database_object.add_row, vargs, time_spent=last_time)

        _, last_time = easy_function_test(
            'Get timestamp', database_object.get_timestamps, {}, time_spent=last_time)

        vargs = {
            'received_bytes' : 0,
            'send_bytes' : 0,
        }
        _, last_time = easy_function_test(
            'Get last value', database_object.get_last_value, vargs, time_spent=last_time)

        _, last_time = easy_function_test(
            'Check new day', database_object.check_new_day, {}, time_spent=last_time)

        _, last_time = easy_function_test(
            'Check new month', database_object.check_new_month, {}, time_spent=last_time)

        if os.path.isfile(TEST_FILE):
            os.remove(TEST_FILE)
        end_test_case('Database', time_spent)
    except Exception as ex:
        print(ex)
        end_test_case('Database', time_spent, success=False)

if __name__ == '__main__':
    test_logger()
    test_interface()
    test_database()
