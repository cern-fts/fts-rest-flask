import logging
import socket
import time
from datetime import datetime
from threading import Thread

from fts3rest.model import Host
from fts3rest.model.meta import Session

log = logging.getLogger(__name__)


class Heartbeat(Thread):
    """
    Keeps running on the background updating the db marking the process as alive
    """

    def __init__(self, tag, interval):
        """
        Constructor
        """
        Thread.__init__(self)
        self.tag = tag
        self.interval = interval
        self.daemon = True

    def run(self):
        """
        Thread logic
        """
        host = Host(hostname=socket.getfqdn(), service_name=self.tag,)

        while self.interval:
            host.beat = datetime.utcnow()
            try:
                Session.merge(host)
                Session.commit()
                log.debug("Hearbeat")
            except Exception as e:
                log.warning("Failed to update the heartbeat: %s" % str(e))
            time.sleep(self.interval)
