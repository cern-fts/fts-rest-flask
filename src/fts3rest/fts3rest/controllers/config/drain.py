#   Copyright Members of the EMI Collaboration, 2013.
#   Copyright 2013-2020 CERN
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


from fts3.model import *
from fts3rest.model.meta import Session
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.accept import accept
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from werkzeug.exceptions import BadRequest, NotFound
from flask import request, Response
from fts3rest.controllers.config import audit_configuration

log = logging.getLogger(__name__)


"""
Drain operations
"""


@authorize(CONFIG)
@jsonify
def set_drain():
    """
    Set the drain status of a server
    """
    input_dict = get_input_as_dict(request)

    hostname = input_dict.get("hostname", None)
    drain = input_dict.get("drain", True)
    if not isinstance(drain, bool) or not isinstance(hostname, str):
        raise BadRequest("Invalid drain request")

    entries = Session.query(Host).filter(Host.hostname == hostname).all()
    if not entries:
        raise BadRequest("Host not found")

    try:
        audit_configuration(
            "drain", "Turning drain %s the drain mode for %s" % (drain, hostname)
        )
        for entry in entries:
            entry.drain = drain
            Session.merge(entry)
        Session.commit()
    except Exception:
        Session.rollback()
        raise
