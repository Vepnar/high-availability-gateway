from . import logger, processor
from datetime import datetime 
import sqlite3
import os.path
import time

db = None

def enable():
    global db
    # Check if the database is enabled
    if not processor.config.getboolean('DATABASE','enabled'):
        return
    file = processor.config.get('DATABASE','file')
    try:

        # Check if the database exists
        if os.path.isfile(file):
            logger.debug('Database loaded')
            db = sqlite3.connect(file)
            return

        logger.debug('Creating new database file')

        # Create a new database and add records for this day
        db = sqlite3.connect(file)
        db.execute('''CREATE TABLE RECORDS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL,\
        SPECIAL INTEGER NOT NULL)
        ''')

        # Add day table
        db.execute('''CREATE TABLE DAYLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')

        # Add month table
        db.execute('''CREATE TABLE MONTHLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')


        # Commit changed
        db.commit()
        logger.debug('Database loaded')
    
    # Print an error message when something went wrong
    except:
        processor.config.set('DATABASE','enabled','False')
        logger.err('Can\'t open the database. Check if this user has permissions to write')
    
def get_last_value():
    global db
    
    # Check if the database is enabeld
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0

    # Execute sql command
    sql = f'SELECT RECIEVED, SEND FROM RECORDS WHERE TIMESTAMP = (SELECT MAX(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    # Data from previous day if available 
    if output is None:
        sql = f'SELECT RECIEVED, SEND FROM DAYLOGS WHERE TIMESTAMP = (SELECT MAX(TIMESTAMP)  FROM RECORDS);'
        output = db.execute(sql).fetchone()
        
        # Return nothing if this ain't found either
        if output is None:
            return 0,0

        # Return values from last day
        return output[0], output[1]

    # Return last values from today
    return output[0], output[1]

def get_start_value():
    global db
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0,0

    # Get values of first moment of today
    sql = f'SELECT TIMESTAMP,RECIEVED,SEND FROM RECORDS WHERE TIMESTAMP = (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    # Return 0,0,0 when there are no values captured today
    if output is None:
        return 0,0,0
    
    # Return timestamp, recieved bytes and send bytes 
    return output[0], output[1], output[2]

# Add new values to today's record
# RX, TX, Time, special = captured on startup
def add_row(recieved,send,timestamp=None,special=0):

    # Check if the database is enabled
    if not processor.config.getboolean('DATABASE','enabled'):
        return

    # Set timestamp in miliseconds if it ain't set yet
    if timestamp is None:
        timestamp = int(round(time.time()))
    
    # Add data to today's records
    sql = 'INSERT INTO RECORDS (TIMESTAMP, RECIEVED, SEND, SPECIAL) ' \
        f'VALUES({timestamp}, {recieved}, {send},{special});'
    try:

        # Try execute the sql and commit the data
        db.execute(sql)
        db.commit()
    except:

        # Print an error and disable the database option
        logger.err('Couldn\'t write to the database')
        processor.config.set('DATABASE','enabled','False')

# Purge and compress old data
# This will make some free space when there is limited space
def move_old_data(rx, tx):

    # Check if the database is enabled return start values when the database is disabled
    if not processor.config.getboolean('DATABASE','enabled'):
        return rx,tx

    old_timestamp, _, _ = get_start_value()

    # Recieve latest value in today's records
    recieved, send = get_last_value()

    if old_timestamp == 0:
        return recieved, send

    # Check if there is a new day
    old_date = datetime.fromtimestamp(old_timestamp)
    new_date = datetime.now()
    timestamp = int(round(datetime.timestamp(new_date)))

    # Check if we are in a new month
    if old_date.month is not new_date.month:

        # Set new month values
        recieved, send = get_last_value()
        sql = 'INSERT INTO MONTHLOGS (TIMESTAMP, RECIEVED, SEND) ' \
        f'VALUES({timestamp}, {recieved}, {send});'
        db.execute(sql)

        # Delete old in today's logs and day logs
        db.execute('DELETE FROM RECORDS')
        db.execute('DELETE FROM DAYLOGS')

        try:
            # Try to commit changes and intercept an error when it is found
            db.commit()
            logger.debug('New month! old information has been purged and stored in a more compact way')
        except:
            # Print an error and disable the database option
            logger.err('Couldn\'t write to the database')
            processor.config.set('DATABASE','enabled','False')
        
        # Reset counter
        return 0, 0

    # Check if we are in a new day
    if abs(new_date - old_date).days < 1:
        return recieved, send

    # Create new row in daylogger
    sql = 'INSERT INTO DAYLOGS (TIMESTAMP, RECIEVED, SEND) ' \
        f'VALUES({timestamp}, {recieved}, {send});'

    # Add new row to day logger and remove all information about today
    db.execute(sql)
    db.execute('DELETE FROM RECORDS')

    try:
        # Try to commit changes and intercept an error when it is found
        db.commit()
        logger.debug('New day! old information has been purged and stored in a more compact way')
    except:
        # Print an error and disable the database option
        logger.err('Couldn\'t write to the database')
        processor.config.set('DATABASE','enabled','False')
    

    return 0, 0
    

    