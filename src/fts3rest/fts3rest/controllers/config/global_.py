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
from fts3rest.lib.helpers.jsonify import jsonify, to_json
from fts3rest.lib.helpers.accept import accept
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from werkzeug.exceptions import BadRequest, NotFound
from flask import request, Response
from fts3rest.controllers.config import audit_configuration, validate_type


log = logging.getLogger(__name__)


"""
Server-wide configuration
"""


@authorize(CONFIG)
@accept(html_template="/config/global.html")
def get_global_config():
    """
    Get the global configuration
    """
    # Only retry, is bound to VO, the others are global (no VO)
    rows = Session.query(ServerConfig).all()
    result = {"*": ServerConfig()}
    for r in rows:
        if r:
            if r.vo_name in (None, "*"):
                result["*"] = r
            else:
                result[r.vo_name] = r
    return result


@authorize(CONFIG)
@jsonify
def set_global_config():
    """
    Set the global configuration
    """
    cfg = get_input_as_dict(request)

    vo_name = cfg.get("vo_name", "*")
    db_cfg = Session.query(ServerConfig).get(vo_name)
    if not db_cfg:
        db_cfg = ServerConfig(vo_name=vo_name)

    for key, value in cfg.iteritems():
        value = validate_type(ServerConfig, key, value)
        setattr(db_cfg, key, value)

    Session.merge(db_cfg)
    audit_configuration("set-globals", to_json(db_cfg, indent=None))
    try:
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return get_global_config()


@authorize(CONFIG)
@jsonify
def delete_vo_global_config():
    """
    Delete the global configuration for the given VO
    """
    input_dict = get_input_as_dict(request, from_query=True)
    vo_name = input_dict.get("vo_name")
    if not vo_name or vo_name == "*":
        raise BadRequest("Missing VO name")

    try:
        Session.query(ServerConfig).filter(ServerConfig.vo_name == vo_name).delete()
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)
