from . import logger, processor
from datetime import datetime 
import sqlite3
import os.path
import time

# Create a global database variable. so this module can access is from everywere.
db = None

# This is where the database will initialize.
def enable(loop):
    # We first start by accessing the global variable database.
    global db

    # Then we access the config which is stored in the processor module.
    # We check if the database module is enabled and cancel the initialization when it's not.
    if not processor.config.getboolean('DATABASE','enabled'):
        return

    # Now we need to now the name of the database. we get it from the global config file.
    file = processor.config.get('DATABASE','file')

    # From now one we will execute every single piece of code in a safe environment.
    try:

        # The first check we do is if the database file exists.
        if os.path.isfile(file):
            
            # When the file exists we message the used that the database is loaded and connect to the database their file.
            logger.debug('Database loaded')
            db = sqlite3.connect(file)
            return

        # When need to create a new database file because it doesn't exist.
        # We first start by logging to the user about the fact that it doesn't exist.
        logger.debug('Creating new database file')

        # Now we connect to the database file.
        db = sqlite3.connect(file)

        # We can't use it yes because there are no tables in the database.
        # We first create a table for the records of today.
        db.execute('''CREATE TABLE RECORDS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECEIVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL,\
        SPECIAL INTEGER NOT NULL)
        ''')

        # Then we will create a table with the daily logs.
        db.execute('''CREATE TABLE DAYLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECEIVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')

        # And the last thing we add is the monthly logs.
        db.execute('''CREATE TABLE MONTHLOGS ( \
        TIMESTAMP INTEGER NOT NULL PRIMARY KEY, \
        RECEIVED INTEGER NOT NULL, \
        SEND INTEGER NOT NULL)
        ''')

        # After all those tables are added we need to commit all our changes!
        # Now our database is done and ready for usage!
        db.commit()

        # We message our great news to the terminal.
        logger.debug('Database loaded')
    
    except:
        # There occur some errors for example when we don't have permissions to write.
        # We message to the user about the writing problem and disable the database module.
        # The module will be turned on again when you restart the application.
        processor.config.set('DATABASE','enabled','False')
        logger.err('Can\'t open the database. Check if this user has permissions to write')

# This function will receive the total amount of network usage from the database.
def get_last_value():
    
    # Then we check if this module is enabled and return 0,0 when it ain't enabled.
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0

    # We now need to access our database. You can only access a database with sql commands.
    # This command will ask for the an item in our records table with the highest timestamp.
    # Which means that it will get the latest added item from our database.
    # After the command is processed we execute it and receive only 1 item.
    sql = 'SELECT RECEIVED, SEND FROM RECORDS WHERE TIMESTAMP = (SELECT MAX(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    # Here we check if the command we executed before actually gave us any rows.
    if output is None:
        # It looks like it didn't gave us any rows that means there are no rows in the records table.
        # We now look in the daylog table to see if there are any rows in there.
        # We do the same as in the other SQL command but now for the DAYLOGS table.
        sql = 'SELECT RECEIVED, SEND FROM DAYLOGS WHERE TIMESTAMP = (SELECT MAX(TIMESTAMP)  FROM RECORDS);'
        output = db.execute(sql).fetchone()
        
        # We check if this SQL commands returns anything.
        if output is None:
            # Looks like there is also nothing in this table. So we return 0,0 to let them know that everything is empty.
            return 0,0

        # But we return data when its found in our DAYLOGS table.
        return output[0], output[1]

    # And this is the same for the records table. return it when its found.
    return output[0], output[1]

# Here we access the first value added to todays records.
# TODO delete this function and replace it
def get_start_value():

    # Then we need to check if the database module is enabled and return 3 zeros when it's not.
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0,0

    # Now we prepare another SQL command to ask for the first item added to the records of today
    # After that we execute the command and receive only 1 value. the first one added
    sql = 'SELECT TIMESTAMP,RECEIVED,SEND FROM RECORDS WHERE TIMESTAMP = (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    # Now we check if there is anything added today, and return 3 zeros when it's not
    if output is None:
        return 0,0,0
    
    # It looks like we got some information from the database so we return it!
    return output[0], output[1], output[2]

# This function get the first item in the todays records and get its timestamp it will also do that to daily records
def get_timestamps():

    # First we need to check if the database module is enabled and return 3 zeros when it's not.
    if not processor.config.getboolean('DATABASE','enabled'):
        return 0,0

    # initialize default timestamp for today and daily
    today = 0
    daily = 0

    # Now we prepare another SQL command to ask for the first item added to the records of today.
    # After that we execute the command and receive only 1 value. the first one added.
    sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP = (SELECT MIN(TIMESTAMP)  FROM RECORDS);'
    output = db.execute(sql).fetchone()

    # Check if there is something in todays records.
    if output is not None:
        # Set todays timestamp to the timestamp found the todays records.
        today = output[0]

    # Now we need to do the same thing as before but for the daily records.
    sql = 'SELECT TIMESTAMP FROM RECORDS WHERE TIMESTAMP = (SELECT MIN(TIMESTAMP)  FROM DAYLOGS);'
    output = db.execute(sql).fetchone()

    # Check if there is something in this daily records.
    if output is not None:
        # Set the daily timestamp to the timestamp found in the database.
        daily = output[0]

    # Return the today and daily timestamp for later use.
    return today, daily

# This is the function that will add the data to the database.
# To be specific to the todays record tables.
def add_row(received,send,timestamp=None,special=0):
    # Then we check if this module is enabled.
    if not processor.config.getboolean('DATABASE','enabled'):
        return

    # Now we check if the function who called us gave us a time variable.
    if timestamp is None:
        # Looks like we don't got any :(
        # So we have to make our own from time and convert it to an integer because time by default returns a float.
        timestamp = int(time.time())
    
    # Now we need to prepare a sql with our timestamp, received bytes send bytes and our special tag in it.
    # The special tag is currently only for showing the database when the system booted.
    sql = 'INSERT INTO RECORDS (TIMESTAMP, RECEIVED, SEND, SPECIAL) ' \
        f'VALUES({timestamp}, {received}, {send},{special});'

    # Now we enter a safe environment because there could be some things that could go wrong here.
    # For example when we don't have any writing rights or when the disk is full.
    try:
        # Now we execute the SQL command and commit our changes to the database.
        db.execute(sql)
        db.commit()

    # Like I said before there could go some things wrong.
    # Those things get handled here by sending a message in the terminal.
    except:
        logger.warn('Couldn\'t write to the database')

# This function will keep track of the current day and the current month.
# It will move data and delete data so the database doesn't get too big.
def move_old_data(rx, tx):

    # First of all we check if this module is enabled in the config file and return the receive and send values when it's not.
    if not processor.config.getboolean('DATABASE','enabled'):
        return rx,tx

    # First of all we need to see when the first row was added today and the first row added to the daily table.
    # So we call the first row and receive their timestamps.
    today_timestamp, daily_timestamp = get_timestamps()

    # Return the receive and send values when the timestamp returns zero. This only happens when there is no row found.
    if today_timestamp == 0:
        return rx, tx

    # Now we convert the timestamp received from the database to a datetime so we can use it in later calculations.
    today_date = datetime.fromtimestamp(today_timestamp)
    daily_date = datetime.fromtimestamp(daily_timestamp)

    # Here we get our received and send data from the database. We don't need it right now but it will be usefull later.
    received, send = get_last_value()

    # We also need a datetime from now and convert it to a timestamp.
    # The timestamp is used later for formatting into SQL commands.
    new_date = datetime.now()
    timestamp = int(datetime.timestamp(new_date))

    # Now we compare the current month with the month stored in the daily record table.
    if new_date.month is not daily_date.month and daily_timestamp is not 0:
        # We are in a new month when they're not the same so we have to move our daily records to or monthly records and clear out all the records made today.
        
        # Here we format the values we got earlier into one new sql command.
        # This command will add a new row in the monthly records.
        sql = 'INSERT INTO MONTHLOGS (TIMESTAMP, RECEIVED, SEND) ' \
        f'VALUES({timestamp}, {received}, {send});'
        db.execute(sql)

        # Here we delete the rows in the daily and todays records.
        db.execute('DELETE FROM RECORDS')
        db.execute('DELETE FROM DAYLOGS')

        # Now we access a safe environment to commit the values to the database and intercept any error when it occurs.
        # Try to commit changes and intercept an error when it is found.
        try:
            db.commit()

            # Show our great news to the terminal, because we are nice guys! :)
            logger.debug('New month! old information has been purged and stored in a more compact way')

        # It doesn't always goes the we want it
        # This error only crashes when the program doesn't have access to write to the database or someone else is using it,
        # We print the message to the console so someone will see it and will take care of it
        except:
            logger.warn('Couldn\'t write to the database')
        
        # Return 2 zeros to reset the current monthly counter
        return 0, 0

    # Here we compare the current day with the day we received in the database.
    if abs(new_date - today_date).days < 1:
        # When the difference is less than 1 we will return the received bytes and the send bytes.
        # Less than one means today
        return rx, tx

    # When it is more than 1 we need to add a new row to the daily logger.
    # We start by making an new sql command with todays timestamp, the received bytes, and the send bytes.
    sql = 'INSERT INTO DAYLOGS (TIMESTAMP, RECEIVED, SEND) ' \
        f'VALUES({timestamp}, {received}, {send});'

    # Now we execute the just crafted sql command and delete all values stored in todays records.
    db.execute(sql)
    db.execute('DELETE FROM RECORDS')

    # We access our safe environment again to commit our database changes without messing everything up
    try:
        db.commit()
        
        # We send a message to the console again because we are nice and great <3
        logger.debug('New day! old information has been purged and stored in a more compact way')

    # This commit could go wrong so we send the error message the the user in the terminal
    except:
        logger.warn('Couldn\'t write to the database')
    
    # Return the received bytes and the send bytes so it can be used later
    return rx, tx
    

    