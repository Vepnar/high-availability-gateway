# Author: Arjan de Haan (Vepnar)

from . import logger, database, interface, mailing, mqtt
from contextlib import suppress
import configparser
import asyncio
import time

# Here we store a global config file. all modules can access this file
config = None

# Create variables to store the total amount of network usage so the other modules can access it easily
total_rx, total_tx = 0, 0

async def measure_loop():
    global total_rx, total_tx
    # This is the actual loop where this program loops trough all its gatherd data and processes it
    # We first start by settings up starting values

    # We start by moving our old data to another table.
    # And receive the total receive and send numbers.
    # Receive and send will be 0 when we are in a month, because we measure network usage per month.
    total_rx, total_tx = database.get_last_value(0, 0)

    # Here we receive the amount of data received and send by the interface.
    # This data is parsed for the ifconfig command and only works on 1 interface.
    # You can set this up in the config file.
    last_rx, last_tx = interface.receive_values()

    # Here we get the delay between each measurement this delay is stored in the config.
    delay = config.getint('NETWORK', 'measuredelay')

    # Startonboot is the option that you should enable when this application starts at boot.
    # This application isn't the quickest on the the planet so it could've missed some bytes.
    # That's why this part of the function exists. it adds the missed bytes to the database
    if config.getboolean('NETWORK', 'startonboot'):

        # Here we add all potential missed bytes to our total amount of bytes
        total_rx, total_tx = total_rx + last_rx, total_tx + last_tx

        # We add our missed information to the database and send a "special=1" value to let the database know that we just booted
        # This could be usefull later on when we are inspecting our data
        database.add_row(total_rx, total_tx, special=1)

        # Here we will print our usage to the user in the terminal
        interface.print_usage(total_rx, total_tx)

        # And now we wait for our set delay
        await asyncio.sleep(delay)

    # This is the infinite loop were we all waited for
    while(True):

        # First we start by capturing new data from our dear interface
        new_rx, new_tx = interface.receive_values()

        # Now we calculate the difference between our new values and our old values
        calc_rx, calc_tx = new_rx - last_rx, new_tx - last_tx

        # Set our calculated values on zero when they're negative because negative numbers ain't welcome in our database
        calc_tx = calc_tx if calc_tx > 0 else 0
        calc_rx = calc_rx if calc_rx > 0 else 0

        # After that we add our calculated values and add them to our total network usage.
        # We send the sum of those values to the database wo checks if there is a new month and check if our counters should be resetted
        total_rx, total_tx = database.get_last_value(
            total_rx+calc_rx, total_tx+calc_tx)

        # Set our new measurements as our old measurements
        last_rx, last_tx = new_rx, new_tx

        # Add our new total network usage to our database
        database.add_row(total_rx, total_tx)

        # Send our total data and our calculated data to the MQTT module
        # This will send the data to adafruit so you can see the status of this program from another device
        mqtt.update_data(calc_rx, calc_tx, total_tx+total_rx)

        # There is also an option to disable an interface when we hit an certain threshold
        interface.check_disabletrigger(total_rx+total_tx)

        # And almost the last thing we have to do! We print the data to the terminal with some pretty colours
        interface.print_usage(total_rx, total_tx)

        # And now the last thing!!! We wait a set amount of time before we start this loop again
        await asyncio.sleep(delay)

def start():
    # This is where it all starts
    global config

    # First we need to start by making an asynchronous loop
    async_loop = asyncio.get_event_loop()

    # After that we need to parse the config file.
    # The file that we will be parsing is "config.cfg" we print a nice debug message after we are done parsing the file.
    config = configparser.ConfigParser()
    config.read('_.cfg')
    logger.debug('Config loaded')

    # Now we start each module one by one
    # This will only initialize the modules and not actually loop them
    # Each module can be disabled in the config. The module will check if it is disabled by itself in the enable function
    database.enable()
    interface.enable()
    mailing.enable()
    mqtt.enable()

    # After all modules are initialized we will display a message to the user
    logger.log('Measuring started')

    # This is where we start the actual asynchronous loop starts
    # suppress is a better way to ignore a exceptions for example a keyboardinterrupt
    with suppress(KeyboardInterrupt):
        # Add our automatic asynchronous data migrator to the asynchronous loop
        asyncio.ensure_future(database.loop(), loop=async_loop)

        # Start the most important part of the loop
        async_loop.run_until_complete(measure_loop())

    # Close the actual asynchronous to clean everything up and message to the user about the status of the program
    async_loop.close()
    logger.log('Shutting down...')
