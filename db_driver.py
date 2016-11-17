from cassandra.cluster import Cluster
from cassandra.query import dict_factory

import consts


class DB_Driver():

    def connect(self):
        self.cluster = Cluster()
        session = self.cluster.connect(consts.KEYSPACE)
        session.set_keyspace(consts.KEYSPACE)
        session.row_factory = dict_factory
        self.session = session

    def disconnect(self):
        self.session.shutdown()
        self.cluster.shutdown()

    def get_msg(self, msg_id):
        msg = None
        query = "SELECT * FROM found_messages WHERE id=%s"
        rows = self.session.execute(query, [msg_id])
        try:
            msg = rows[0]
        except IndexError:
            return msg
        return msg

    def save_msg(self, msg):
        self.session.execute(
            """
            INSERT INTO found_messages (id, page, msg, msg_creation_time,
                                        email_notification_time,
                                        sms_notification_time,
                                        imessage_notification_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (msg[consts.MSG_ID], msg[consts.PAGE], msg[consts.MSG],
             msg[consts.MSG_CREATION_TIME],
             msg[consts.EMAIL_NOTIFICATION_TIME],
             msg[consts.SMS_NOTIFICATION_TIME],
             msg[consts.IMESSAGE_NOTIFICATION_TIME])
        )

