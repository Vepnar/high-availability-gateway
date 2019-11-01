from . import logger, processor
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

    # Return 0, 0 when there is nothing in the database
    if output is None:
        return 0, 0
    return output[0], output[1]

def add_row(recieved,send,timestamp=None,special=0):
    # Set timestamp in miliseconds if it ain't set yet
    if timestamp is None:
        timestamp = int(round(time.time()*1000))
    
    # Add values to database
    sql = 'INSERT INTO RECORDS (TIMESTAMP, RECIEVED, SEND, SPECIAL) ' \
        f'VALUES({timestamp}, {recieved}, {send},{special});'
    try:
        db.execute(sql)
        db.commit()
    except:
        logger.err('Couldn\'t write to the database')
        processor.config.set('DATABASE','enabled','False')
    

    