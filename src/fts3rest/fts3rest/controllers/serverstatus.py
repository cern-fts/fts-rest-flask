#   Copyright 2015-2020 CERN
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
from fts3rest.model.meta import Session
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import *
from fts3rest.lib.helpers.jsonify import jsonify

"""
Server general status
"""


@require_certificate
@authorize(CONFIG)
@jsonify
def hosts_activity():
    """
    What are the hosts doing
    """
    staging = Session.execute(
        "SELECT COUNT(*), staging_host "
        " FROM t_file "
        " WHERE file_state = 'STARTED' "
        " GROUP BY staging_host"
    )
    response = dict()

    for count, host in staging:
        response[host] = dict(staging=count)

    active = Session.execute(
        "SELECT COUNT(*), transfer_host "
        " FROM t_file "
        " WHERE file_state = 'ACTIVE' "
        " GROUP BY transfer_host"
    )
    for count, host in active:
        if host not in response:
            response[host] = dict()
        response[host]["active"] = count

    return response
