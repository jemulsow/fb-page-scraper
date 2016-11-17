import argparse
import facebook
import datetime
from ConfigParser import SafeConfigParser

import consts
from db_driver import DB_Driver
from email_client import EmailNotificationClient

VERBOSE = False

config = SafeConfigParser()
config.read(consts.CONFIG_FILE)

db_driver = None
email_client = None


def parse_args():
    """
    Defines and parses CLI args
    :param secrets: secrets from config file to use as defaults
    :return: args object of parsed args
    """
    cli_description = ("Runs a query on Facebook public page(s) looking for "
                       "a list of key words, and notifies you if found. "
                       "Accepts a Facebook User Token. Will look in {} if "
                       "not provided. Uses this config file for all other "
                       "options. See README.rst.".format(consts.CONFIG_FILE))
    msg = ("Store the generated long-lived token as {} in {}.".format(
        consts.USER_TOKEN_LL, consts.CONFIG_FILE))
    parser = argparse.ArgumentParser(prog='fb-scraper',
                                     description=cli_description)
    parser.add_argument('-t', '--user_token', required=False,
                        help=msg,
                        default=get_long_lived_token())
    parser.add_argument('-v', '--verbose', required=False,
                        action='store_true', help="Run in verbose mode.")
    return parser.parse_args()


def get_long_lived_token():

    token = None
    try:
        token = config.get(consts.SECRETS_SECTION, consts.USER_TOKEN_LL)
    except:
        pass
    return token


def get_page_names():

    pages = []
    try:
        pages = config.get(consts.FB_QUERY_SECTION, consts.PAGES).split(',')
    except:
        print ("{} is a required comma separated list in the {} section of "
               "{}.".format(consts.PAGES, consts.FB_QUERY_SECTION,
                            consts.CONFIG_FILE))
        exit(1)
    if VERBOSE:
        print ("Querying pages: {}".format(pages))
    return pages


def get_key_words():

    key_words = []
    try:
        key_words = config.get(consts.FB_QUERY_SECTION,
                               consts.KEY_WORDS).split(',')
    except:
        print ("{} is a required comma separated list in the {} section of "
               "{}.".format(consts.KEY_WORDS, consts.FB_QUERY_SECTION,
                            consts.CONFIG_FILE))
        exit(1)
    if VERBOSE:
        print ("Looking for words: {}".format(key_words))
    return key_words


def get_posts_limit():
    """
    Get the number of posts to query from the config file. Default to 10.
    :return: limit
    """
    limit = None
    try:
        limit = config.get(consts.FB_QUERY_SECTION, consts.LIMIT)
    except:
        pass
    if limit is None or limit is '':
        limit = consts.DEFAULT_LIMIT
    else:
        try:
            limit = int(limit)
            if limit > 100:
                print ("ERROR: limit in {} must be an integer between 1 and "
                       "100".format(consts.CONFIG_FILE))
                exit(1)
        except:
            print ("ERROR: limit in {} must be an integer between 1 and "
                   "100".format(consts.CONFIG_FILE))
            exit(1)
        if VERBOSE:
            print "Using limit {} from config.".format(limit)

    return str(limit)


def is_email_notification_enabled():
    """
    Is email notification enabled
    :return: boolean
    """
    enabled = False
    try:
        enabled = config.getboolean(consts.EMAIL_NOTIFICATION_SECTION, consts.ENABLED)
    except:
        pass
    return enabled


def is_sms_notification_enabled():
    """
    Is SMS notification enabled
    :return: boolean
    """
    enabled = False
    try:
        enabled = config.getboolean(consts.SMS_NOTIFICATION_SECTION, consts.ENABLED)
    except:
        pass
    return enabled


def is_imessage_notification_enabled():
    """
    Is iMessage notification enabled
    :return: boolean
    """
    enabled = False
    try:
        enabled = config.getboolean(consts.IMESSAGE_NOTIFICATION_SECTION, consts.ENABLED)
    except:
        pass
    return enabled


def make_request(token, page, limit):
    graph = facebook.GraphAPI(access_token=token, version='2.2')
    f = graph.get_object('{}/feed?limit={}'.format(page, limit))
    return f.get(consts.DATA)


def initialize_db_driver():
    global db_driver
    if db_driver is None:
        db_driver = DB_Driver()
        db_driver.connect()


def notification_sent(msg_id):
    """
    Queries the DB for this message. If found, checks for notification
    timestamps.
    :param msg_id: dictionary of msg attrs
    :return: True of notification already sent, else False
    """
    already_sent = False
    initialize_db_driver()
    msg = db_driver.get_msg(msg_id)
    if (msg is not None and (
        msg.get(consts.EMAIL_NOTIFICATION_TIME) or
        msg.get(consts.SMS_NOTIFICATION_TIME) or
        msg.get(consts.IMESSAGE_NOTIFICATION_TIME)
    )):
        already_sent = True
        print msg
    if VERBOSE:
        print ("Notification for msg {} already sent: {}".format(
                   msg_id, already_sent))
    return already_sent


def save_to_db(msgs):
    """
    Saves this message to the database.
    timestamps.
    :param msgs: list of dictionary of messages
    :return:
    """
    initialize_db_driver()
    for msg in msgs:
        db_driver.save_msg(msg)
        print "Saved msg {} to DB".format(msg)


def notify_by_email(msgs):
    """
    Checks if email notification is enabled, and sends email notification
    :param msgs:
    :return:
    """
    enabled = is_email_notification_enabled()
    if not enabled:
        return
    email_client = EmailNotificationClient()
    email_client.send_email(msgs)
    for msg in msgs:
        msg[consts.EMAIL_NOTIFICATION_TIME] = datetime.datetime.now()


def notify_by_sms(msgs):
    """
    Checks if SMS notification is enabled, and sends SMS notification
    :param msgs:
    :return:
    """
    enabled = is_sms_notification_enabled()
    if not enabled:
        return
    pass


def notify_by_imessage(msgs):
    """
    Checks if iMessage notification is enabled, and sends iMessage notification
    :param msgs:
    :return:
    """
    enabled = is_imessage_notification_enabled()
    if not enabled:
        return
    pass


def parse_response(data, page, key_words):
    found_messages = []
    for d in data:
        message = d.get(consts.MESSAGE, '').lower()
        if any(kw in message for kw in key_words):
            time = d.get(consts.CREATED_TIME)
            msg_id = d.get(consts.MSG_ID)
            msg = {consts.MSG: message,
                   consts.PAGE: page,
                   consts.MSG_CREATION_TIME: time,
                   consts.MSG_ID: msg_id,
                   consts.EMAIL_NOTIFICATION_TIME: None,
                   consts.SMS_NOTIFICATION_TIME: None,
                   consts.IMESSAGE_NOTIFICATION_TIME: None}
            if VERBOSE:
                print ("Found the following msg: {}".format(msg))
            # Check in DB notification has already been sent for message.
            already_notified = notification_sent(msg_id)
            if not already_notified:
                found_messages.append(msg)
    return found_messages


def main():
    # Parse args
    args = parse_args()

    # Save off token
    token = args.user_token
    if token is None:
        print ("ERROR: {} is required. Pass it in or save it in "
               "{}.".format(consts.USER_TOKEN_LL, consts.CONFIG_FILE))
        exit(1)

    # Get log verbosity level
    global VERBOSE
    VERBOSE = args.verbose

    # Get pages to search
    pages = get_page_names()
    limit = get_posts_limit()
    key_words = get_key_words()

    msgs = []
    # For each page, query and process
    for page in pages:
        resp = make_request(token, page, limit)
        found_messages = parse_response(resp, page, key_words)
        if found_messages:
            msgs.extend(found_messages)
    print msgs

    if len(msgs):
        # Notify
        notify_by_email(msgs)
        notify_by_sms(msgs)
        notify_by_imessage(msgs)

        # Save off to DB
        save_to_db(msgs)

if __name__ == "__main__":
    main()
