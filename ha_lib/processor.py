import configparser
from . import logger, database, interface, mailing, mqtt
import time

config = None

def infloop():
    # Set starting values
    total_rx, total_tx = database.move_old_data(*database.get_last_value())
    last_rx, last_tx = interface.recieve_values()
    delay = config.getint('NETWORK', 'measuredelay')

    # Enable rxtxstart when this script runs on startup
    if config.getboolean('NETWORK','rxtxstart'):
        # Clean up old data
        database.move_old_data()
        total_rx, total_tx = total_rx + last_rx, total_tx + last_tx
        database.add_row(total_rx, total_tx, special=1)
        interface.print_usage(total_rx, total_tx)
        time.sleep(delay)

    while(True):
        # Clean up old data

        # Recieve new values
        new_rx, new_tx = interface.recieve_values()

        # Calculate new values for the charts
        calc_rx, calc_tx = new_rx - last_rx, new_tx - last_tx
        total_rx, total_tx = database.move_old_data(total_rx + calc_rx, total_tx + calc_tx)
        last_rx, last_tx = new_rx, new_tx

        # We don't want any negative values in our charts
        calc_tx = calc_tx if calc_tx > 0 else 0
        calc_rx = calc_rx if calc_rx > 0 else 0


        # Add new information to the database
        database.add_row(total_rx, total_tx)
        mqtt.update_data(calc_rx,calc_tx,total_tx+total_rx)
        
        # Check if it should send an Email
        mailing.check_threshold(total_rx,total_tx, calc_rx+calc_tx)
        interface.check_disabletrigger(total_rx+total_tx)

        interface.print_usage(total_rx,total_tx)
        time.sleep(delay)


def start():
    global config
    config = configparser.ConfigParser()
    config.read('config.cfg')
    logger.debug('Config loaded')

    # Start all modules
    database.enable()
    interface.enable()
    mailing.enable()
    mqtt.enable()

    logger.log('Measuring started')

    try:
        infloop()
    except KeyboardInterrupt as e:
        logger.log('Shutting down...')


