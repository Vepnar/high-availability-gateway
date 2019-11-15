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
        # Create a new database and add tabels
        db = sqlite3.connect(file)
        db.execute('''CREATE TABLE RECORDS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL,\
        SPECIAL INTEGER NOT NULL)
        ''')

        # Add day values
        db.execute('''CREATE TABLE DAYLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')

        # Add month values
        db.execute('''CREATE TABLE MONTHLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECIEVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')


        db.commit()
        logger.debug('Database loaded')
    
    # Print an error message if something went wrong
    except:
        processor.config.set('DATABASE','enabled','False')
        logger.err('Can\'t open the database. Check if this user has permissions to write')
    
def get_last_value():
    global db
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

        return output[0], output[1]

    return output[0], output[1]

def get_start_value():
    global db
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0,0

    sql = f'SELECT TIMESTAMP,RECIEVED,SEND FROM RECORDS WHERE TIMESTAMP = (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    if output is None:
        return 0,0,0

    return output[0], output[1], output[2]

def add_row(recieved,send,timestamp=None,special=0):
    # Check if the database is enabled
    if not processor.config.getboolean('DATABASE','enabled'):
        return

    # Set timestamp in miliseconds if it ain't set yet
    if timestamp is None:
        timestamp = int(round(time.time()))
    
    # Add values to database
    sql = 'INSERT INTO RECORDS (TIMESTAMP, RECIEVED, SEND, SPECIAL) ' \
        f'VALUES({timestamp}, {recieved}, {send},{special});'
    try:
        db.execute(sql)
        db.commit()
    except:
        logger.err('Couldn\'t write to the database')
        processor.config.set('DATABASE','enabled','False')

def move_old_data():
    if not processor.config.getboolean('DATABASE','enabled'):
        return

    old_timestamp, _, _ = get_start_value()

    if old_timestamp == 0:
        return

    # Check if there is a new day
    old_date = datetime.fromtimestamp(old_timestamp)
    new_date = datetime.now()
    timestamp = int(round(datetime.timestamp(new_date)))

    if(abs(new_date - old_date).days < 1):
        return

    # Recieve latest value in today's records
    recieved, send = get_last_value()

    # Create new row in daylogger
    sql = 'INSERT INTO DAYLOGS (TIMESTAMP, RECIEVED, SEND) ' \
        f'VALUES({timestamp}, {recieved}, {send});'

    # Add new row to day logger and remove all information about today
    db.execute(sql)
    db.execute('DELETE FROM RECORDS')
    db.commit()

    logger.debug('New day! old information has been purged and stored in a more compact way')

    return
    

    