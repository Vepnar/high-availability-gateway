from Adafruit_IO import MQTTClient as mqtt
from subprocess import Popen, PIPE
from . import logger, processor, database
import sqlite3
import os.path
import struct
import time
import sys

client = None

def enable():
    global client
    # Check if MQTT is enabled
    config = processor.config
    if not config.getboolean('MQTT', 'enabled'):
        return

    # Create client and set username and key
    client = mqtt(config.get('MQTT', 'username'), config.get('MQTT', 'key'))

    # Connect to the server
    try:
        keepalive = config.getint('MQTT', 'keepalive')
        client.connect(keepalive=keepalive)
    except:
        config.set('MQTT', 'enabled', 'False')
        logger.err('Can\'t login into MQTT server')
        sys.exit(0)
    logger.debug('MQTT enabled')

    # Enable mqtt numpad
    if config.getboolean('MQTTNUMPAD', 'enabled'):
        # Set handlers for mqtt numpad
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        client.loop_background()


def update_data(rx, tx, tt):
    # Check if MQTT is enabled
    cfg = processor.config
    if not cfg.getboolean('MQTT', 'enabled'):
        return

    # Convert values to mbits/s
    delay = cfg.getint('NETWORK', 'MeasureDelay')
    rx = rx / 125000.0 / delay
    tx = tx / 125000.0 / delay
    tt = tt / 1000000.0
    tt_today = -1

    # Calculate today's usage based on values in the database
    # This function doesnt work when the database option is disabled
    start_values = database.get_start_value()
    if start_values[0] != 0:
        tt_today =  tt-((start_values[0]+ start_values[1]) / 1000000.0)

    # Send values
    try_update_data('recievepath',rx)
    try_update_data('sendpath',tx)
    try_update_data('recieveplussendpath',rx+tx)
    try_update_data('totalnetworkusagepath',tt)
    try_update_data('todaynetworkusagepath', tt_today)

def try_update_data(nick, data):
    global client

    # Recieve path from config file
    path = processor.config.get('MQTT', nick.lower())

    # Cancel execution when there is no path found
    if path is None:
        return

    # Don't publish anything when the data is negative
    if 0 > data:
        return

    # Publish data on specified path
    # Round values to 2 digits
    client.publish(path,round(data,2))

# Some nice disconnect message
def on_disconnect(client):
    logger.warn('MQTT disconnected!')


def on_connect(client):
    # Subscribe on the numpad
    client.subscribe(processor.config.get('MQTTNUMPAD', 'subcribepath'))
    logger.debug('MSQTTNumpad loaded')


# Recieve packets from the MQTT server
def on_message(client, feed_id, payload):
    

    # Check is command is added in the config file
    if not f'command{payload}' in processor.config['MQTTNUMPAD']:
        logger.warn(f'Numpad {payload} is pressed but there is no command')
        return

    # Execute command when found
    # TODO add more functionality within the application
    Popen(processor.config.get('MQTTNUMPAD',
                               f'command{payload}'), shell=True, stdout=PIPE)
    logger.debug(f'Numpad {payload} is executed')
