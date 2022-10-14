#   Copyright 2022 CERN
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

from flask import request
from werkzeug.exceptions import BadRequest

from fts3rest.model import File, FileActiveStates
from fts3rest.model.meta import Session

from fts3rest.lib.http_exceptions import *
from fts3rest.lib.middleware.fts3auth.authorization import (
    authorized,
    authorize,
    require_certificate,
)
from fts3rest.lib.middleware.fts3auth.constants import CONFIG
from fts3rest.lib.helpers.jsonify import jsonify

import json

"""
Admin Commands
"""


@require_certificate
@authorize(CONFIG)
@jsonify
def force_start_files():
    """
    Force start individual files - accepts a (json) list of file_ids
    """

    if request.content_type == "application/json":
        try:
            file_ids = json.loads(request.data)
        except Exception:
            raise BadRequest("Malformed input")
    else:
        raise BadRequest("Only accepts 'Content-Type: application/json'")

    if (not isinstance(file_ids, list)) or (
        not all(isinstance(file_id, int) for file_id in file_ids)
    ):
        raise BadRequest("Only accepts a list of integer fileIDs")

    messages = []
    try:
        for file_id in file_ids:
            file = Session.query(File).get(file_id)
            if not file:
                messages.append({"file_id": file_id, "error": "File does not exist"})
                continue

            if file.file_state != "SUBMITTED":
                messages.append(
                    {"file_id": file_id, "error": "File is not in SUBMITTED state"}
                )
                continue

            file.file_state = "FORCE_START"
            Session.merge(file)
        Session.commit()
    except Exception:
        Session.rollback()
        raise

    return messages
