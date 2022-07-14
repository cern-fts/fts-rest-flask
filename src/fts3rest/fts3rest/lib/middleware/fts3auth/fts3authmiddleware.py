#   Copyright  Members of the EMI Collaboration, 2013.
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

from fts3rest.model.meta import Session
from fts3rest.model import BannedDN
from .credentials import UserCredentials, InvalidCredentials
from sqlalchemy.exc import DatabaseError
from urllib.parse import urlparse
from werkzeug.exceptions import Unauthorized, Forbidden, HTTPException


log = logging.getLogger(__name__)


class FTS3AuthMiddleware:
    """
    Pylons middleware to wrap the authentication as part of the request
    process.
    """

    def __init__(self, wrap_app, config):
        self.app = wrap_app
        self.config = config

    def _trusted_origin(self, environ, parsed):
        allow_origin = environ.get("ACCESS_CONTROL_ORIGIN", None)
        if not allow_origin:
            return False
        return parsed.scheme + "://" + parsed.netloc == allow_origin

    def _validate_origin(self, environ):
        origin = environ.get("HTTP_ORIGIN", None)
        if not origin:
            log.debug("No Origin header found")
            return
        parsed = urlparse(origin)
        if parsed.netloc != environ.get("HTTP_HOST"):
            if not self._trusted_origin(environ, parsed):
                raise Forbidden("Host and Origin do not match")
            log.info("Trusted Origin: %s://%s" % (parsed.scheme, parsed.netloc))

    def _get_credentials(self, environ):
        try:
            credentials = UserCredentials(
                environ, self.config["fts3.Roles"], self.config
            )
        except InvalidCredentials as e:
            raise Forbidden("Invalid credentials (%s)" % str(e))

        if not credentials.user_dn:
            raise Unauthorized("A valid X509 certificate or proxy is needed")

        if not self._has_authorized_vo(credentials):
            raise Forbidden("The user does not belong to any authorized vo")

        if self._is_banned(credentials):
            raise Forbidden("The user has been banned")

        return credentials

    def __call__(self, environ, start_response):
        try:
            self._validate_origin(environ)
            credentials = self._get_credentials(environ)
            environ["fts3.User.Credentials"] = credentials
            log.info("%s logged in via %s" % (credentials.user_dn, credentials.method))
        except HTTPException as e:
            log.exception(e)
            return e(environ, start_response)
        except DatabaseError as e:
            log.warning(
                "Database error when trying to get user's credentials: %s" % str(e)
            )
            Session.remove()
            raise
        except Exception as e:
            log.warning(
                "Unexpected error when trying to get user's credentials: %s" % str(e)
            )
            raise
        else:
            return self.app(environ, start_response)

    def _has_authorized_vo(self, credentials):
        if "*" in self.config["fts3.AuthorizedVO"]:
            return True
        for v in credentials.vos:
            if v in self.config["fts3.AuthorizedVO"]:
                log.info("Authorized VO: %s" % str(v))
                return True
        return False

    def _is_banned(self, credentials):
        banned = Session.query(BannedDN).get(credentials.user_dn)
        return banned is not None
