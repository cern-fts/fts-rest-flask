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
from urllib.parse import urlparse

from flask import request, Response
from werkzeug.exceptions import BadRequest

from fts3.model import *
from fts3rest.controllers.config import audit_configuration
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import authorize
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from fts3rest.model.meta import Session

log = logging.getLogger(__name__)


"""
VO Share configuration
"""


@authorize(CONFIG)
@jsonify
def set_share():
    """
    Add or modify a share
    """
    input_dict = get_input_as_dict(request)
    source = input_dict.get("source")
    destination = input_dict.get("destination")
    vo = input_dict.get("vo")
    try:
        share = int(input_dict.get("share"))
        if share < 0:
            raise BadRequest("Shares values cannot be negative")
    except Exception:
        raise BadRequest("Bad share value")

    if not source or not destination or not vo or not share:
        raise BadRequest("Missing source, destination, vo and/or share")

    source = urlparse(source)
    if not source.scheme or not source.hostname:
        raise BadRequest("Invalid source")
    source = "%s://%s" % (source.scheme, source.hostname)

    destination = urlparse(destination)
    if not destination.scheme or not destination.hostname:
        raise BadRequest("Invalid source")
    destination = "%s://%s" % (destination.scheme, destination.hostname)

    try:
        share_cfg = ShareConfig(
            source=source, destination=destination, vo=vo, share=share
        )
        Session.merge(share_cfg)
        audit_configuration(
            "share-set",
            "Share %s, %s, %s has been set to %d" % (source, destination, vo, share),
        )
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return share


@authorize(CONFIG)
@jsonify
def get_shares():
    """
    List the existing shares
    """
    return Session.query(ShareConfig).all()


@authorize(CONFIG)
@jsonify
def delete_share():
    """
    Delete a share
    """
    input_dict = get_input_as_dict(request, from_query=True)
    source = input_dict.get("source")
    destination = input_dict.get("destination")
    vo = input_dict.get("vo")

    if not source or not destination or not vo:
        raise BadRequest("Missing source, destination and/or vo")

    try:
        share = Session.query(ShareConfig).get((source, destination, vo))
        if share:
            Session.delete(share)
            audit_configuration(
                "share-delete",
                "Share %s, %s, %s has been deleted" % (source, destination, vo),
            )
            Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)
