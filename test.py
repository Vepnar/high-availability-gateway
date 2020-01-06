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
    output = progress(task, time_spent=time_spent)
    try:
        function(**args)
        return (output, time.time())
    except Exception as ex:
        if time_spent is None:
            time_spent = 0
        else:
            time_spent = time.time() - time_spent
        print(ex)
        end_test_case('Logger', time_spent, success=False)
        return (None, time.time())


def test_logger():
    """Terminal logger tester:
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
            'file_logging': False
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
            'logging_file': TEST_FILE
        }
        if os.path.isfile(TEST_FILE):
            os.remove(TEST_FILE)

        last_time = progress('Creating file testing object', last_time)
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


if __name__ == '__main__':
    test_logger()
