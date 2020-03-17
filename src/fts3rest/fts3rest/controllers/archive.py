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

from werkzeug.exceptions import NotFound, Forbidden
from flask import jsonify

from fts3.model import ArchivedJob
from fts3rest.model.meta import Session
from fts3rest.lib.middleware.fts3auth.authorization import authorized
from fts3rest.lib.middleware.fts3auth.constants import *


def index():
    """
    Just give the operations that can be performed
    """
    ret = {
        "_links": {
            "curies": [{"name": "fts", "href": "https://gitlab.cern.ch/fts/fts3"}],
            "fts:archivedJob": {
                "href": "/archive/{id}",
                "title": "Archived job information",
                "templated": True,
            },
        }
    }
    return jsonify(ret)


def _get_job(job_id):
    job = Session.query(ArchivedJob).get(job_id)
    if job is None:
        raise NotFound('No job with the id "%s" has been found in the archive' % job_id)
    if not authorized(TRANSFER, resource_owner=job.user_dn, resource_vo=job.vo_name):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    return job


def get(job_id):
    """
    Get the job with the given ID
    """
    job = _get_job(job_id)
    # Trigger the query, so it is serialized
    files = job.files
    return job


def get_field(job_id, field):
    """
    Get a specific field from the job identified by id
    """
    job = _get_job(job_id)
    if hasattr(job, field):
        return getattr(job, field)
    else:
        raise NotFound("No such field")
