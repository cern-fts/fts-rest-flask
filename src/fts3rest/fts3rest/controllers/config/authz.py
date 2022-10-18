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

from flask import request, Response
from werkzeug.exceptions import BadRequest

from fts3rest.model import *
from fts3rest.controllers.config import audit_configuration
from fts3rest.lib.helpers.accept import accept
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import ADMIN, CONFIG
from fts3rest.model.meta import Session

log = logging.getLogger(__name__)


"""
Static authorizations
"""


@require_certificate
@authorize(CONFIG)
@jsonify
def add_authz():
    """
    Give special access to someone
    """
    input_dict = get_input_as_dict(request)
    dn = input_dict.get("dn")
    op = input_dict.get("operation")
    if not dn or not op:
        raise BadRequest("Missing dn and/or operation")
    if op == ADMIN:
        raise BadRequest("'%s' level can only be changed via database access" % ADMIN)

    try:
        authz = Session.query(AuthorizationByDn).get((dn, op))
        if not authz:
            authz = AuthorizationByDn(dn=dn, operation=op)
            audit_configuration("authorize", '%s granted to "%s"' % (op, dn))
            Session.merge(authz)
            Session.commit()
    except Exception:
        Session.rollback()
        raise

    return authz


@require_certificate
@authorize(CONFIG)
@accept(html_template="/config/authz.html")
def list_authz():
    """
    List granted accesses
    """
    input_dict = get_input_as_dict(request, from_query=True)
    dn = input_dict.get("dn")
    op = input_dict.get("operation")
    authz = Session.query(AuthorizationByDn)
    if dn:
        authz = authz.filter(AuthorizationByDn.dn == dn)
    if op:
        authz = authz.filter(AuthorizationByDn.operation == op)
    return authz.all()


@require_certificate
@authorize(CONFIG)
def remove_authz():
    """
    Revoke access for a DN for a given operation, or all
    """
    input_dict = get_input_as_dict(request, from_query=True)
    dn = input_dict.get("dn")
    op = input_dict.get("operation")
    if not dn:
        raise BadRequest("Missing DN parameter")
    if op == ADMIN:
        raise BadRequest("'%s' level can only be changed via database access" % ADMIN)

    to_be_removed = (
        Session.query(AuthorizationByDn)
        .filter(AuthorizationByDn.operation != ADMIN)
        .filter(AuthorizationByDn.dn == dn)
    )
    if op:
        to_be_removed = to_be_removed.filter(AuthorizationByDn.operation == op)

    try:
        to_be_removed.delete()
        if op:
            audit_configuration("revoke", '%s revoked for "%s"' % (op, dn))
        else:
            audit_configuration("revoke", 'All revoked for "%s"' % dn)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return Response([""], status=204)
