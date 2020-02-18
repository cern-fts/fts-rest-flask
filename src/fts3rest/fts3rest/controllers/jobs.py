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

from flask import request, Response, jsonify
from werkzeug.exceptions import Forbidden, BadRequest

from datetime import datetime, timedelta
from requests.exceptions import HTTPError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import noload


import json
import logging

from fts3.model import Job, File, JobActiveStates, FileActiveStates
from fts3.model import DataManagement, DataManagementActiveStates
from fts3.model import Credential, FileRetryLog
from fts3rest.model.meta import Session

from fts3rest.lib.http_exceptions import *
from fts3rest.lib.middleware.fts3auth.constants import *

log = logging.getLogger(__name__)

"""
Operations on jobs and transfers
"""


def index():
    """
    Get a list of active jobs, or those that match the filter requirements
    """
    user = request.environ["fts3.User.Credentials"]

    jobs = Session.query(Job)

    filter_dn = request.values.get("user_dn", None)
    filter_vo = request.values.get("vo_name", None)
    filter_dlg_id = request.values.get("dlg_id", None)
    filter_state = request.values.get("state_in", None)
    filter_source = request.values.get("source_se", None)
    filter_dest = request.values.get("dest_se", None)
    filter_fields = request.values.get("fields", None)
    try:
        filter_limit = int(request.values["limit"])
    except Exception:
        filter_limit = None
    try:
        components = request.values["time_window"].split(":")
        hours = components[0]
        minutes = components[1] if len(components) > 1 else 0
        filter_time = timedelta(hours=int(hours), minutes=int(minutes))
    except Exception:
        filter_time = None

    if filter_dlg_id and filter_dlg_id != user.delegation_id:
        raise Forbidden("The provided delegation id does not match your delegation id")
    if filter_dn and filter_dn != user.user_dn:
        raise BadRequest(
            "The provided DN and delegation id do not correspond to the same user"
        )
    if filter_limit is not None and filter_limit < 0 or filter_limit > 500:
        raise BadRequest("The limit must be positive and less or equal than 500")

    # Automatically apply filters depending on granted level
    granted_level = user.get_granted_level_for(TRANSFER)
    if granted_level == PRIVATE:
        filter_dlg_id = user.delegation_id
    elif granted_level == VO:
        filter_vo = user.vos[0]
    elif granted_level == NONE:
        raise Forbidden("User not allowed to list jobs")

    if filter_state:
        filter_state = filter_state.split(",")
        jobs = jobs.filter(Job.job_state.in_(filter_state))
        if filter_limit is None:
            if filter_time is not None:
                filter_not_before = datetime.utcnow() - filter_time
                jobs = jobs.filter(Job.job_finished >= filter_not_before)
            else:
                jobs = jobs.filter(Job.job_finished == None)
    else:
        jobs = jobs.filter(Job.job_finished == None)

    if filter_dn:
        jobs = jobs.filter(Job.user_dn == filter_dn)
    if filter_vo:
        jobs = jobs.filter(Job.vo_name == filter_vo)
    if filter_dlg_id:
        jobs = jobs.filter(Job.cred_id == filter_dlg_id)
    if filter_source:
        jobs = jobs.filter(Job.source_se == filter_source)
    if filter_dest:
        jobs = jobs.filter(Job.dest_se == filter_dest)

    if filter_limit:
        jobs = jobs.order_by(Job.submit_time.desc())[:filter_limit]
    else:
        jobs = jobs.yield_per(100).enable_eagerloads(False)

    if filter_fields:
        original_jobs = jobs

        def _field_subset():
            fields = filter_fields.split(",")
            for job in original_jobs:
                entry = dict()
                for field in fields:
                    if hasattr(job, field):
                        entry[field] = getattr(job, field)
                yield entry

        return Response(_field_subset(), mimetype="application/json")
    else:
        return jsonify(jobs)


def get():
    pass


def get_files():
    pass


def cancel_files():
    pass


def cancel_all_by_vo():
    pass


def cancel_all():
    pass


def get_file_retries():
    pass


def get_dm():
    pass


def get_field():
    pass


def cancel():
    pass


def modify():
    pass


def submit():
    pass
