#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module to access the database
Author: Arjan de Haan (Vepnar)
Last edited: 6 January 2020"""

import sys
import time
import sqlite3
import os.path
import asyncio
from datetime import datetime

class Database:
    """Handle all the database functions.
    args:
        logger: (logger)
        enabled: (boolean) enabled when this module is enabled
        database_file: (str) path to database file
        data_update_interval: (int) interval to check if we are in a new day
        exit_on_crash: (boolean) exit module when crashes
    """

    def __init__(self, logger, enabled, database_file,
                 exit_on_crash=True, data_update_interval=36000):
        self.logger = logger
        self.enabled = enabled
        self.data_update_interval = data_update_interval

        if not enabled:
            return

        sql = '''
        CREATE TABLE RECORDS (
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY,
        RECEIVED INTEGER NOT NULL, SEND INTEGER NOT NULL, SPECIAL INTEGER NOT NULL);
        CREATE TABLE DAYLOGS (
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, RECEIVED INTEGER
        NOT NULL, SEND INTEGER NOT NULL); 
        CREATE TABLE MONTHLOGS (
        TIMESTAMP INTEGER NOT
        NULL PRIMARY KEY, RECEIVED INTEGER NOT NULL, SEND INTEGER NOT NULL);
        '''

        try:
            if os.path.isfile(database_file):
                self.logger.debug('Database loaded')
                self.database = sqlite3.connect(database_file)
                return
            self.logger.debug('Creating new database file')
            self.database = sqlite3.connect(database_file)
            self.database.executescript(sql)
            self.database.commit()
            self.logger.debug('Database loaded')

        except sqlite3.Error:
            if exit_on_crash:
                sys.exit(-1)
            else:
                raise Exception
            self.logger.err(
                'Can\'t open the database. Check if this user has permissions to write')

    def get_last_value(self, received_bytes=0, send_bytes=0, throw=False):
        """Receive total amount of network usage from the database.

        Will access RECORDS table in the database to receive data about the total usage.
        It will do the same for DAYLOGS when there is no data in the RECORDS table.

        Args:
            received_bytes: total amount of bytes received today.
            send_bytes: total amount of bytes send today.
            throw: throw an error when an error occurs
        Return:
            Total received bytes according to the database.
            Total send bytes according to the database
        """

        if not self.enabled:
            if throw:
                raise Exception
            return received_bytes, send_bytes

        sql = 'SELECT RECEIVED, SEND FROM RECORDS WHERE TIMESTAMP =\
            (SELECT MAX(TIMESTAMP) FROM RECORDS);'
        output = self.database.execute(sql).fetchone()

        if output is None:  # Access daylogs when there is nothing found in records
            sql = 'SELECT RECEIVED, SEND FROM DAYLOGS WHERE TIMESTAMP =\
                (SELECT MAX(TIMESTAMP) FROM DAYLOGS);'
            output = self.database.execute(sql).fetchone()
            if output is None:
                return 0, 0
            return output[0], output[1]
        return output[0], output[1]

    # Is this used??
    def get_start_value(self):
        """Receive today's starting value
        Returns:
            Received bytes
            Send bytes
        """
        if not self.enabled:
            return 0, 0, 0
        sql = '''
        SELECT
        RECEIVED,SEND 
        FROM RECORDS 
        WHERE
        TIMESTAMP =(SELECT MIN(TIMESTAMP) FROM RECORDS);
        '''

        output = self.database.execute(sql).fetchone()
        if output is None:
            return 0, 0
        return output[0], output[1]


    def get_timestamps(self):
        """Receive daily timestamp and record's timestamp
        Returns:
            record: timestamp of the first records in today logs.
            daily: timestamp of the first record in the daily logs.
        """
        record, daily = 0, 0

        # Receive the first timestamp of the records table.
        sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP=\
            (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
        output = self.database.execute(sql).fetchone()
        if output is not None:
            record = output[0]

        # Receive the first row in the daily logs
        sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP =\
            (SELECT MIN(TIMESTAMP)  FROM DAYLOGS);'
        output = self.database.execute(sql).fetchone()
        if output is not None:
            daily = output[0]
        return record, daily

    def add_row(self, received, send, timestamp=None, special=0, throw=False):
        """Adds new information to the database

        Args:
            received: amount of bytes received.
            send: amount of bytes send.
            timestamp: timestamp when this is information is captured.
            special:
                0 = nothing special.
                1 = captured on startup.
            throw: throw exception when an error occurs
        """
        if not self.enabled:
            return False

        if timestamp is None:
            timestamp = int(time.time())

        sql = 'INSERT INTO RECORDS (TIMESTAMP, RECEIVED, SEND, SPECIAL) ' \
            f'VALUES({timestamp}, {received}, {send},{special});'
        try:
            self.database.execute(sql)
            self.database.commit()
            return True
        except sqlite3.Error:
            if not throw:
                self.logger.warn('Couldn\'t write to the database')
            else:
                raise Exception
        return False

    async def loop(self):
        """Asynchronous infinite loop to update the database.
        This means that i'll delete old information.
        """

        if not self.enabled:
            return
        if self.data_update_interval < 6:
            return
        while True:
            await asyncio.sleep(self.data_update_interval)
            if not self.check_new_month():
                self.check_new_day()

    def check_new_day(self, throw=False):
        """Function to check if we are in a new day
        Args:
            throw: (boolean) throw exception when something goes wrong.
        """
        record_timestamp, _ = self.get_timestamps()
        record_date = datetime.fromtimestamp(record_timestamp)
        received, send = self.get_last_value(0, 0)
        timestamp = int(time.time())
        new_date = datetime.now()

        if throw: # Set 32 days back for the testing module
            timestamp -= 165888000

        if record_timestamp == 0:
            if throw:
                raise sqlite3.Error
            return False

        # Check if we are in a new day.
        if abs(new_date - record_date).days < 1:
            if throw:
                raise sqlite3.Error
            return False

        sql = 'INSERT INTO DAYLOGS (TIMESTAMP, RECEIVED, SEND) ' \
            f'VALUES({timestamp}, {received}, {send});'
        self.database.execute(sql)
        self.database.execute('DELETE FROM RECORDS')
        try:
            self.database.commit()
            self.logger.debug(
                'New day! old information has been purged and stored in a more compact way')
            return True
        except sqlite3.Error:
            self.logger.warn('Couldn\'t write to the database')
            if throw:
                raise sqlite3.Error
        return False

    def check_new_month(self, throw=False):
        """Function to check if we are in a new month
        Args:
            throw: (boolean) throw exception when something goes wrong.
        """
        _, daily_timestamp = self.get_timestamps()
        daily_date = datetime.fromtimestamp(daily_timestamp)

        received, send = self.get_last_value(0, 0)
        new_date = datetime.now()
        timestamp = int(time.time())

        if not new_date.month != daily_date.month and daily_timestamp != 0:
            if throw:
                raise Exception
            return False

        sql = 'INSERT INTO MONTHLOGS (TIMESTAMP, RECEIVED, SEND) ' \
            f'VALUES({timestamp}, {received}, {send});'
        self.database.execute(sql)
        self.database.execute('DELETE FROM RECORDS')
        self.database.execute('DELETE FROM DAYLOGS')
        try:
            self.database.commit()
            self.logger.debug(
                'New month! old information has been purged and stored in a more compact way')
            return True
        except sqlite3.Error:
            self.logger.warn('Couldn\'t write to the database')
            if throw:
                raise sqlite3.Error
            return False
