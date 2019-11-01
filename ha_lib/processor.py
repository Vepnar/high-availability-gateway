import configparser
from . import logger, database, interface, mailing
import time

config = None

def infloop():
    total_rx, total_tx = database.get_last_value()
    last_rx, last_tx = interface.recieve_values()
    delay = config.getint('NETWORK', 'measuredelay')

    if config.getboolean('NETWORK','rxtxstart'):
        total_rx, total_tx = total_rx + last_rx, total_tx + last_tx
        database.add_row(total_rx, total_tx, special=1)
        interface.print_usage(total_rx, total_tx)
        time.sleep(delay)

    while(True):
        new_rx, new_tx = interface.recieve_values()
        calc_rx, calc_tx = new_rx - last_rx, new_tx - last_tx
        total_rx, total_tx = total_rx + calc_rx, total_tx + calc_tx

        # Add new information to the database
        database.add_row(total_rx, total_tx)
        
        # Check if it should send an Email
        mailing.check_threshold(total_rx,total_tx, calc_rx+calc_tx)

        interface.print_usage(total_rx,total_tx)
        time.sleep(delay)


def start():
    global config
    config = configparser.ConfigParser()
    config.read('config.cfg')
    logger.debug('Config loaded')
    database.enable()
    interface.enable()
    mailing.enable()

    logger.log('Measuring started')

    try:
        infloop()
    except KeyboardInterrupt as e:
        logger.log('Shutting down...')


