#   Copyright 2020 CERN
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
from re import T
import socket
import time
import random
from datetime import date, datetime, timedelta
from threading import Thread, current_thread


from fts3rest.model.meta import Session
from fts3rest.lib.openidconnect import oidc_manager
from fts3rest.model import Credential, Host

from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)


class IAMTokenRefresher(Thread):
    """
    Daemon thread that refreshes all access tokens in the DB at every interval.

    Keeps running on the background updating the DB, marking the process as alive.
    There should be ONLY ONE across all instances.
    Keep in mind that with the Apache configuration line
        WSGIDaemonProcess fts3rest python-path=... processes=2 threads=15
    there will be 2 instances of the application per server, meaning we need to check that there is only one
    IAMTokenRefresher per host, and only one between all hosts.

    The SQLAlchemy scoped_session is thread-safe
    """

    def __init__(self, tag, config):
        Thread.__init__(self)
        self.daemon = (
            True  # The thread will immediately exit when the main thread exits
        )
        self.tag = tag
        self.hostname = socket.getfqdn()
        self.refresh_interval = int(
            config.get("fts3.TokenRefreshDaemonIntervalInSeconds", 600)
        )
        self.hearbeat = int(config.get("fts3.HeartBeatInterval", 60))

    def start_thread(self, rest_name):
        # Check if there is an active token refresher in the DB
        token_refresher = (
            Session.query(Host)
            .filter(
                Host.service_name == self.tag,
                Host.beat
                > datetime.utcnow() - timedelta(seconds=3 * self.refresh_interval),
            )
            .all()
        )
        if not token_refresher:
            # If there is no active token refresher check if current host is the first in the instance
            host = (
                Session.query(Host)
                .filter(
                    Host.service_name == rest_name,
                    Host.beat
                    > datetime.utcnow() - timedelta(seconds=5 * self.hearbeat),
                )
                .order_by(Host.service_name)
                .first()
            )
            if host and host.hostname == self.hostname:
                return True
        return False

    def run(self):
        """
        Regularly check if there is another active IAMTokenRefresher in the DB. If not, become the active thread.
        """
        log.debug("CREATE THREAD ID: {}".format(current_thread().ident))
        # Initial sleep to make sure the heartbeat thread has already started and registered all the hosts in the DB
        time.sleep(2 * self.hearbeat)  # nosec
        # The interval at which the thread will check if there is another active thread.
        db_check_interval = 3 * self.refresh_interval
        while True:
            rest_name = "fts_rest"
            if self.start_thread(rest_name):
                log.debug("Activating IAMTokenRefresher thread")
                threads = (
                    Session.query(Host).filter(Host.service_name == self.tag).all()
                )
                for thread in threads:
                    # Delete
                    Session.delete(thread)
                    Session.commit()
                    log.debug("Delete inactive thread")

                host = Host(hostname=self.hostname, service_name=self.tag)
                log.debug("New token refresher thread created")
                while True:
                    host.beat = datetime.utcnow()
                    log.debug(
                        "THREAD ID: {}, beat {}".format(
                            current_thread().ident, host.beat
                        )
                    )
                    try:
                        h2 = Session.merge(host)
                        Session.commit()
                        log.debug(
                            "fts-token-refresh-daemon heartbeat {}".format(h2.beat)
                        )
                    except SQLAlchemyError as ex:
                        log.warning(
                            "Failed to update the fts-token-refresh-daemon heartbeat: %s"
                            % str(ex)
                        )
                        Session.rollback()
                        raise

                    credentials = (
                        Session.query(Credential)
                        .filter(Credential.proxy.notilike("%CERTIFICATE%"))
                        .all()
                    )
                    Session.commit()
                    log.debug("{} credentials to refresh".format(len(credentials)))
                    for credential in credentials:
                        try:
                            credential = oidc_manager.refresh_access_token(credential)
                            log.debug(
                                "OK refresh_access_token (exp=%s)"
                                % str(credential.termination_time)
                            )
                            Session.merge(credential)
                            Session.commit()
                        except SQLAlchemyError as ex:
                            log.warning(
                                "Failed to update refresh token for dn: %s because: %s"
                                % (str(credential.dn), str(ex))
                            )
                            Session.rollback()
                        except Exception as ex:
                            if credential.termination_time <= datetime.utcnow():
                                Session.delete(credential)
                                Session.commit()
                                log.warning(
                                    "Deleting token for dn: %s refreshing failed because: %s"
                                    % (str(credential.dn), str(ex))
                                )
                            else:
                                log.warning(
                                    "Failed to refresh token for dn: %s because: %s"
                                    % (str(credential.dn), str(ex))
                                )
                    time.sleep(self.refresh_interval)
            else:
                log.debug("THREAD ID: {}".format(current_thread().ident))
                log.debug("Another thread is active -- Going to sleep")
                time.sleep(db_check_interval)
