from Adafruit_IO import MQTTClient as mqtt
from subprocess import Popen, PIPE
from . import logger, processor
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

    # Set handlers
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Connect to the server
    try:
        keepalive = config.getint('MQTT', 'keepalive')
        client.connect(keepalive=keepalive)
    except:
        config.set('MQTT', 'enabled', 'False')
        logger.err('Can\'t login into MQTT server')
        sys.exit(0)
    logger.debug('MQTT enabled')

    if config.getboolean('MQTTNUMPAD', 'enabled'):
        client.loop_background()


def update_data(rx, tx, tt):
    global client

    # Check if MQTT is enabled
    cfg = processor.config
    if not cfg.getboolean('MQTT', 'enabled'):
        return

    # Convert values to mbits/s
    delay = cfg.getint('NETWORK', 'MeasureDelay')
    rx = round(rx / 125000.0 / delay, 2)
    tx = round(tx / 125000.0 / delay, 2)
    tt = round(tt / 1000000, 2)

    # Send values
    client.publish(cfg.get('MQTT', 'recievepath'), rx)
    client.publish(cfg.get('MQTT', 'sendpath'), tx)
    client.publish(cfg.get('MQTT', 'RecievePlusSendPath'), rx+tx)
    client.publish(cfg.get('MQTT', 'totalnetworkusagepath'), tt)


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
    Popen(processor.config.get('MQTTNUMPAD',
                               f'command{payload}'), shell=True, stdout=PIPE)
    logger.debug(f'Numpad {payload} is executed')
