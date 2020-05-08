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
import json
import logging
from urllib.parse import unquote

from flask import request, Response
from werkzeug.exceptions import BadRequest, NotFound

from fts3rest.model import *
from fts3rest.controllers.config import audit_configuration
from fts3rest.lib.helpers.accept import accept
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import authorize
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from fts3rest.model.meta import Session

log = logging.getLogger(__name__)


"""
Link configuration
"""


@authorize(CONFIG)
@jsonify
def set_link_config():
    """
    Set the configuration for a given link
    """
    input_dict = get_input_as_dict(request)

    source = input_dict.get("source", "*")
    destination = input_dict.get("destination", "*")
    symbolicname = input_dict.get("symbolicname", None)

    if not symbolicname:
        raise BadRequest("Missing symbolicname")

    link_cfg = (
        Session.query(LinkConfig)
        .filter(LinkConfig.symbolicname == symbolicname)
        .first()
    )

    try:
        min_active = int(input_dict.get("min_active", 2))
        max_active = int(input_dict.get("max_active", 2))
    except Exception as e:
        raise BadRequest("Active must be an integer (%s)" % str(e))

    if not source or not destination:
        raise BadRequest("Missing source and/or destination")

    if min_active is None:
        raise BadRequest("Missing min_active")
    if max_active is None:
        raise BadRequest("Missing max_active")
    if min_active > max_active:
        raise BadRequest("max_active is lower than min_active")

    if not link_cfg:
        link_cfg = LinkConfig(
            source=source,
            destination=destination,
            symbolicname=symbolicname,
            min_active=min_active,
            max_active=max_active,
        )

    for key, value in input_dict.items():
        setattr(link_cfg, key, value)

    audit_configuration("link", json.dumps(input_dict))

    Session.merge(link_cfg)
    try:
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return link_cfg


@authorize(CONFIG)
@accept(html_template="/config/links.html")
def get_all_link_configs():
    """
    Get a list of all the links configured
    """
    return Session.query(LinkConfig).all()


@authorize(CONFIG)
@jsonify
def get_link_config(sym_name):
    """
    Get the existing configuration for a given link
    """
    sym_name = unquote(sym_name)
    link = Session.query(LinkConfig).filter(LinkConfig.symbolicname == sym_name).first()
    if not link:
        raise NotFound("Link %s does not exist" % sym_name)
    return link


@authorize(CONFIG)
@jsonify
def delete_link_config(sym_name):
    """
    Deletes an existing link configuration
    """
    try:
        sym_name = unquote(sym_name)
        Session.query(LinkConfig).filter(LinkConfig.symbolicname == sym_name).delete()
        audit_configuration("link-delete", "Link %s has been deleted" % sym_name)
        Session.commit()
    except:
        Session.rollback()
        raise
    return Response([""], status=204)
