import smtplib
import json
import os
from datetime import datetime
from . import processor, logger, interface


def enable():
    # Check if module is enabled
    if not processor.config.getboolean('EMAIL', 'enabled'):
        return

    file = processor.config.get('EMAIL', 'file')

    # Check if email file exists
    if not os.path.isfile(file):
        processor.config.set('EMAIL', 'enabled', 'False')
        logger.err(f'Email template "{file}" doesnt exist')
        return

    # Check read access on file
    if not os.access(file, os.R_OK):
        processor.config.set('EMAIL', 'enabled', 'False')
        logger.err(f'No read access on "{file}"')
        return

    # Test email formatter
    # There could be some problems with the config you didn't configure right
    try:
        format_email(0,0,0)
    except Exception as e:
        processor.config.set('EMAIL', 'enabled', 'False')
        print(e)
        logger.err('E-Mail formatter crashes')

    # Connect to the SMTP server
    server = connect(enable_run=True)
    if server is None:
        return

    # Don't login when login is disabled
    if not processor.config.getboolean('EMAIL', 'login'):
        server.quit()
        logger.debug('Mailing loaded')
        return

    # Login in the mailing server
    login(server, enable_run=True)
    server.quit()
    logger.debug('Mailing loaded')


def connect(enable_run=False):

    # Recieve connection information
    host = processor.config.get('EMAIL', 'host')
    port = processor.config.get('EMAIL', 'port')
    ssl = processor.config.getboolean('EMAIL', 'ssl')
    timeout = processor.config.getint('EMAIL', 'timeout')

    try:
        # Connect with ssl if enabled
        if ssl:
            return smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            return smtplib.SMTP(host, port, timeout=timeout)
    except:
        # Print errors when can't connect
        if enable_run:
            logger.err('Can\'t connect to the smtp server')
            processor.config.set('EMAIL', 'enabled', 'False')
        else:
            logger.warn('Couldn\'t connect to the smtp server')


def login(server, enable_run=False):

    # Check if login is required
    if not processor.config.getboolean('EMAIL', 'login'):
        return True

    # Recieve login information
    username = processor.config.get('EMAIL', 'username')
    password = processor.config.get('EMAIL', 'password')

    try:
        server.login(username, password)
        return True
    except:
        # Print errors when there are some
        if enable_run:
            logger.err('Can\'t login in the smtp server')
            processor.config.set('EMAIL', 'enabled', 'False')
        else:
            logger.warn('Couldn\'t login in the smtp server')
            return False

# Generate all values we want in our email
def format_email(rx, tx, last):

    # Convert rx and tx to some pretty values
    # And recieve time
    rx_int, rx_unit = interface.byte_formatter(rx)
    tx_int, tx_unit = interface.byte_formatter(tx)
    tt_int, tt_unit = interface.byte_formatter(rx+tx)
    now = datetime.now()

    # Open email file and read lines
    path = processor.config.get('EMAIL', 'file')
    f = open(path, 'r')
    content = f.readlines()
    content = '\n'.join(x.strip() for x in content)

    # Create values to format into the email
    values = {
        'last': last,
        'user': processor.config.get('EMAIL', 'clientname'),
        'rx_int': rx_int,
        'rx_unit': rx_unit,
        'tx_int': tx_int,
        'tx_unit': tx_unit,
        'tt_int': tt_int,
        'tt_unit': tt_unit,
        'time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%d %B %Y')
    }

    # Close open file
    f.close()

    # Format values and return output
    return content.format(**values)

    # netstatistics workstation

def send_email(server, message):
    # Recieve sender, reciever and subject information
    sender = processor.config.get('EMAIL','username')
    reciever = processor.config.get('EMAIL','emailreciever')
    subject = processor.config.get('EMAIL','subject')


    try:
        # Format the email with headers
        msg = f'From: {sender}\nTo: {reciever}\nMIME-Version:1.0\nContent-type:text/html\nSubject: {subject}\n{message}'
        # Send the email
        server.sendmail(sender,reciever,msg)
        return True
    except:
        return False

def check_threshold(rx,tx,last):
    # Check if this module is enabled
    if not processor.config.getboolean('EMAIL', 'enabled'):
        return

    # Recieve/calculate values
    total = rx+tx
    threshold = processor.config.getint('EMAIL','NotificationThreshold')

    # Check if the usage is above the threshold
    if total > threshold:
        server = connect()

        # Check if logged in
        if not login(server):
            return

        message = format_email(rx,tx,last)

        logger.debug('Sending threshold E-Mail')
        # Check if the email is send
        if not send_email(server,message):
            logger.warn('Couldn\'t send the threshold E-Mail')
            return

        logger.log('Threshold E-Mail send!')
        # Update settings when the email is send
        if processor.config.getboolean('EMAIL','resetaftertrigger'):
            processor.config.set('EMAIL','NotificationThreshold',threshold*2)
            logger.debug('E-Mail notification threshold resetted')
            return

        # Disable any future emails
        logger.debug('Disabeld any further E-Mail notifications')
        processor.config.set('EMAIL','enabled','False')
        