import smtplib
from ConfigParser import SafeConfigParser

import consts

config = SafeConfigParser()
config.read(consts.CONFIG_FILE)


class EmailNotificationClient():

    def send_email(self, msgs):
        from_addr = self._get_from_address()
        to_addrs = self._get_to_addresses()
        text = self._format_msgs(msgs)
        subject = "FB Scraper Found Message!"

        message = """From: %s\nTo: %s\nSubject: %s\n\n%s
        """ % (from_addr, to_addrs, subject, text)
        try:
            print "Connecting to gmail smtp server"
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()

            gmail_user = self._get_gmail_user()
            gmail_token = self._get_gmail_token()
            print "Logging in: user: {} token: {}".format(gmail_user, gmail_token)
            server.login(gmail_user, gmail_token)
            print "Sending email: {}".format(message)
            server.sendmail(from_addr, to_addrs, message)
            server.close()
        except Exception:
            raise

    def _get_gmail_user(self):
        try:
            user = config.get(consts.EMAIL_NOTIFICATION_SECTION, consts.USER)
            return user
        except:
            print ("'{}' must be set in the email notification section "
                   "in {}".format(consts.USER, consts.CONFIG_FILE))
            exit(1)
            pass

    def _get_gmail_token(self):
        try:
            token = config.get(consts.EMAIL_NOTIFICATION_SECTION, consts.TOKEN)
            return token
        except:
            print ("'{}' must be set in the email notification section "
                   "in {}".format(consts.TOKEN, consts.CONFIG_FILE))
            exit(1)
            pass

    def _get_to_addresses(self):
        try:
            to = config.get(consts.EMAIL_NOTIFICATION_SECTION, consts.TO)
            return to
        except:
            print ("'{}' must be set in the email notification section "
                   "in {}".format(consts.TO, consts.CONFIG_FILE))
            exit(1)
            pass

    def _get_from_address(self):
        try:
            from_address = config.get(consts.EMAIL_NOTIFICATION_SECTION, consts.FROM)
            return from_address
        except:
            print ("'{}' must be set in the email notification section "
                   "in {}".format(consts.FROM, consts.CONFIG_FILE))
            exit(1)
            pass

    def _format_msgs(self, msgs):
        msg_str = ""
        for msg in msgs:
            msg_segment = (
                "{}: {}: {}\n\n".format(msg[consts.PAGE],
                                        msg[consts.MSG_CREATION_TIME],
                                        msg[consts.MSG]))
            msg_str += msg_segment
        return msg_str

