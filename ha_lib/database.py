"""Module to access the database """

import time
import sqlite3
import os.path
import asyncio
from datetime import datetime
from . import logger, processor

DB = None


def enable():
    """
    This is where the database will initialize.
    After that we run some basic checks to confirm that everything is running like it should.
    """
    global DB

    # Then we access the config which is stored in the processor module.
    # We check if the database module is enabled and cancel the initialization when it's not.
    if not processor.config.getboolean('DATABASE', 'enabled'):
        return

    file = processor.config.get('DATABASE', 'file')
    try:
        if os.path.isfile(file):
            logger.debug('Database loaded')
            DB = sqlite3.connect(file)
            return
        logger.debug('Creating new database file')
        DB = sqlite3.connect(file)
        DB.executescript('''CREATE TABLE RECORDS(TIMESTAMP INTEGER NOT NULL PRIMARY KEY, RECEIVED\
            INTEGER NOT NULL, SEND INTEGER NOT NULL, SPECIAL INTEGER NOT NULL); CREATE TABLE \
            DAYLOGS (TIMESTAMP INTEGER NOT NULL PRIMARY KEY, RECEIVED INTEGER NOT NULL, SEND \
            INTEGER NOT NULL); CREATE TABLE MONTHLOGS (TIMESTAMP INTEGER NOT NULL PRIMARY \
            KEY, RECEIVED INTEGER NOT NULL, SEND INTEGER NOT NULL);
        ''')
        DB.commit()
        logger.debug('Database loaded')

    except sqlite3.Error:
        processor.config.set('DATABASE', 'enabled', 'False')
        logger.err(
            'Can\'t open the database. Check if this user has permissions to write')


def get_last_value(received_bytes=0, send_bytes=0):
    """Receive total amount of network usage from the database.

    Will access RECORDS table in the database to receive data about the total usage.
    It will do the same for DAYLOGS when there is no data in the RECORDS table.

    Args:
        received_bytes: total amount of bytes received today.
        send_bytes: total amount of bytes send today.
    Return:
        Total received bytes according to the database.
        Total send bytes according to the database
    """

    if not processor.config.getboolean('DATABASE', 'enabled'):
        return received_bytes, send_bytes
    sql = 'SELECT RECEIVED, SEND FROM RECORDS WHERE TIMESTAMP =\
         (SELECT MAX(TIMESTAMP) FROM RECORDS);'
    output = DB.execute(sql).fetchone()

    if output is None:  # Access daylogs when there is nothing found in records
        sql = 'SELECT RECEIVED, SEND FROM DAYLOGS WHERE TIMESTAMP =\
             (SELECT MAX(TIMESTAMP) FROM DAYLOGS);'
        output = DB.execute(sql).fetchone()
        if output is None:
            return 0, 0
        return output[0], output[1]
    return output[0], output[1]


def get_start_value():
    """Receive today's starting value
    Returns:
        Received bytes
        Send bytes
    """
    if not processor.config.getboolean('DATABASE', 'enabled'):
        return 0, 0, 0
    sql = 'SELECT RECEIVED,SEND FROM RECORDS WHERE TIMESTAMP =\
         (SELECT MIN(TIMESTAMP) FROM RECORDS);'
    output = DB.execute(sql).fetchone()
    if output is None:
        return 0, 0
    return output[0], output[1]


def get_timestamps():
    """Receive daily timestamp and record's timestamp
    Returns:
        today: timestamp of the first records in today logs
        daily: timestamp of the first record in the daily logs
    """
    today, daily = 0, 0
    if not processor.config.getboolean('DATABASE', 'enabled'):
        return today, daily

    # Receive the first timestamp of today.
    sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP =\
         (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
    output = DB.execute(sql).fetchone()
    if output is not None:
        today = output[0]
    # Receive the first row in the daily logs
    sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP =\
         (SELECT MIN(TIMESTAMP)  FROM DAYLOGS);'
    output = DB.execute(sql).fetchone()
    if output is not None:
        daily = output[0]
    return today, daily


def add_row(received, send, timestamp=None, special=0):
    """Adds new information to the database

    Args:
        received: amount of bytes received.
        send: amount of bytes send.
        timestamp: timestamp when this is information is captured.
        special:
            0 = nothing special.
            1 = captured on startup.
    """
    if not processor.config.getboolean('DATABASE', 'enabled'):
        return

    if timestamp is None:
        timestamp = int(time.time())

    sql = 'INSERT INTO RECORDS (TIMESTAMP, RECEIVED, SEND, SPECIAL) ' \
        f'VALUES({timestamp}, {received}, {send},{special});'
    try:
        DB.execute(sql)
        DB.commit()
    except sqlite3.Error:
        logger.warn('Couldn\'t write to the database')

async def loop():
    """Asynchronous infinite loop to update the database.
    This means that i'll delete old information."""

    if not processor.config.getboolean('DATABASE', 'enabled'):
        return
    interval = processor.config.getint('DATABASE', 'datamoveinterval')
    if interval < 6:
        return

    # The infinite loop
    while True:
        await asyncio.sleep(interval)
        today_timestamp, daily_timestamp = get_timestamps()
        if today_timestamp == 0:
            continue
        # Convert dates
        today_date = datetime.fromtimestamp(today_timestamp)
        daily_date = datetime.fromtimestamp(daily_timestamp)
        received, send = get_last_value(0, 0)
        new_date = datetime.now()
        timestamp = int(datetime.timestamp(new_date))

        # Check if we are in a new month.
        if new_date.month != daily_date.month and daily_timestamp != 0:
            sql = 'INSERT INTO MONTHLOGS (TIMESTAMP, RECEIVED, SEND) ' \
                f'VALUES({timestamp}, {received}, {send});'
            DB.execute(sql)
            DB.execute('DELETE FROM RECORDS')
            DB.execute('DELETE FROM DAYLOGS')
            try:
                DB.commit()
                logger.debug(
                    'New month! old information has been purged and stored in a more compact way')
            except sqlite3.Error:
                logger.warn('Couldn\'t write to the database')
            continue

        # Check if we are in a new day.
        if abs(new_date - today_date).days < 1:
            continue

        sql = 'INSERT INTO DAYLOGS (TIMESTAMP, RECEIVED, SEND) ' \
            f'VALUES({timestamp}, {received}, {send});'
        DB.execute(sql)
        DB.execute('DELETE FROM RECORDS')
        try:
            DB.commit()
            logger.debug(
                'New day! old information has been purged and stored in a more compact way')
        except sqlite3.Error:
            logger.warn('Couldn\'t write to the database')
