import smtplib
import json
import os
from datetime import datetime
from . import processor, logger, interface
import asyncio

def enable():
    # TODO add better documentation
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
        format_email(0, 0, 0)
    except Exception as e:
        processor.config.set('EMAIL', 'enabled', 'False')
        print(e)
        logger.err('E-Mail formatter crashes')

    # Connect to the SMTP server
    server = connect_to_smtp(enable_run=True)
    if server is None:
        return

    # Don't login when login is disabled
    if not processor.config.getboolean('EMAIL', 'login'):
        server.quit()
        logger.debug('Mailing loaded')
        return

    # Login in the mailing server
    login_to_smtp(server, enable_run=True)
    server.quit()

    threshold = processor.config.get('EMAIL', 'NotificationThreshold')
    processor.config.set('EMAIL', 'OGNotificationThreshold', threshold)

    logger.debug('Mailing loaded')


def connect_to_smtp(enable_run=False):
    # Here we try to connect to the smtp server based on the settings set in the config file

    # First we start by receiving connection information from the config file
    host = processor.config.get('EMAIL', 'host')
    port = processor.config.get('EMAIL', 'port')
    ssl = processor.config.getboolean('EMAIL', 'ssl')
    timeout = processor.config.getint('EMAIL', 'timeout')

    # Then we enter a safe environment to catch any unexpected errors
    try:
        # Check if SSL is enabled in the config file and connect with the smtp server with SSL if it is enabled
        if ssl:
            return smtplib.SMTP_SSL(host, port, timeout=timeout)

        # Looks like SSL is not enabled so we connect to the smtp server without it
        return smtplib.SMTP(host, port, timeout=timeout)

    except:
        # Now we need to process any unexpected errors
        # First we check if this run was an enable run because we need to shutdown the module when there are any errors in the enable run
        if enable_run:
            logger.err('Can\'t connect to the smtp server')
            processor.config.set('EMAIL', 'enabled', 'False')
        else:
            # Looks like it isn't an enable run so we just print a warn message
            logger.warn('Couldn\'t connect to the smtp server')


def login_to_smtp(server, enable_run=False):
    # Here we try to login in the smtp server

    # Check if the server isn't None, Because we can't login into something that doesn't exist
    if server is None:
        return False

    # Now we check if logging is in enabled and return true when it is not enabled
    if not processor.config.getboolean('EMAIL', 'login'):
        return True

    # Looks like we need to login into the smtp server
    # So we need to get gather our credential information from the config file
    username = processor.config.get('EMAIL', 'username')
    password = processor.config.get('EMAIL', 'password')

    # Enter the safe environment once again because logging in could fail
    try:
        server.login(username, password)
        # Looks like logging in is successful so we need to return our great news
        return True

    except:
        # An error occurred so we need to handle it
        # We first check if this is an enable run because we need to shutdown the module when there are any errors
        if enable_run:
            logger.err('Can\'t login in the smtp server')
            processor.config.set('EMAIL', 'enabled', 'False')
            return False
        else:

            # Looks like we are not in an enable run and we just return that we can't login
            logger.warn('Couldn\'t login in the smtp server')
            return False


def format_email():
    # This the function where we format all our information in the E-mail HTML file

    # First we get our network usage from the processor
    rx = processor.total_rx
    tx = processor.total_tx

    # Now we format the previously collected information into a prettier piece of text
    rx_int, rx_unit = interface.byte_formatter(rx)
    tx_int, tx_unit = interface.byte_formatter(tx)
    tt_int, tt_unit = interface.byte_formatter(rx+tx)

    # We capture our timestamp for later formatting
    now = datetime.now()

    # Now we are at the part where we actually read the file
    # We start by receiving the path of the file
    path = processor.config.get('EMAIL', 'file')

    # Now we open the file in read only mode
    f = open(path, 'r')

    # After opening it we want to read all lines in the E-Mail file and convert all the lines in 1 big piece of text
    content = f.readlines()
    content = '\n'.join(x.strip() for x in content)

    # Now we don't need the file anymore so we close it
    f.close()

    # This is where we set all our information we want to format into the E-Mail
    values = {
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

    # At last we format all the information into the E-Mail and return it for later use
    return content.format(**values)


def send_email(server, message):
    # This is the function who will add headers to the email and send the email

    # Get information for the headers from the config file
    sender = processor.config.get('EMAIL', 'username')
    receiver = processor.config.get('EMAIL', 'emailreceiver')
    subject = processor.config.get('EMAIL', 'subject')

    try:
        # Now we format our just gathered information + the message into one big message
        email = f'From: {sender}\nTo: {receiver}\nMIME-Version:1.0\nContent-type:text/html\nSubject: {subject}\n{message}'

        # The last thing we have to do is send the E-Mail to the person who should receive it and return our sucess
        server.sendmail(sender, receiver, email)
        return True

    except:
        # Even just sending an E-Mail could go wrong
        return False

async def loop():
    # This is the function who will handle automated emails.

    # We first start by checking if this module is enabled.
    if not processor.config.getboolean('EMAIL', 'enabled'):
        return

    # Receive the interval at what we should check if we reached the treshold.
    interval = processor.config.getint('EMAIL', 'checkinterval')

    # Don't do any checks if the number is below 5 because that will be too many checks and it could overflow the system.
    if interval < 6:
        return

    while True:

        # Wait for a couple of seconds because we don't want to check too fast because that is unnecessary.
        await asyncio.sleep(interval)

        # Receive the threshold value from the config file -1 one means that the threshold is disabled.
        threshold = processor.config.getint('EMAIL', 'NotificationThreshold')
        if threshold > 0:
            continue

        # Receive the amount of received and send bytes and and them together.
        total = processor.total_rx + processor.total_tx

        # Check if the total amount of network usage is more than the threshold.
        # Don't execute any other processing when it doesn't reach the threshold.
        if total < threshold:
            continue

        # Try to connect to the smtp server with the information stored in the config file.
        server = connect_to_smtp()

        # Now we try to login in the smtp server.
        # And print an warning message when it doesn't can't login into the smtp server.
        if not login_to_smtp(server):
            logger.warn(
                'There is an error with the mailing system. please run diagnostics')
            continue

        # Now we start by preparing the E-Mail.
        # We first start by formatting all information into the email and store that as a variable.
        email = format_email()

        # Message the user about the current status
        logger.debug('Sending threshold E-Mail..')

        # Now we try to send the E-Mail and check if it is working
        if not send_email(server, email):

            # Looks like we can't send an E-Mail we should let the user know that we can't do that
            logger.warn('Couldn\'t send the threshold E-Mail')
            continue

        # Looks like our email send! Now we need to let need to let our user in the console now
        logger.log('Threshold E-Mail send!')

        # Update settings when the email is send.
        if processor.config.getboolean('EMAIL', 'resetaftertrigger'):
            
            # Double the threshold and message the user about the update
            processor.config.set('EMAIL', 'NotificationThreshold', threshold*2)
            logger.debug('E-Mail notification threshold has been resetted')
            return

        # Disable any future notification E-Mails and log it to the user
        logger.debug('Disabled any further E-Mail notifications')
        processor.config.set('EMAIL', 'NotificationThreshold', -1)

