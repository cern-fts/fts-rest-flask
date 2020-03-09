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
from werkzeug.exceptions import Forbidden, BadRequest, NotFound, HTTPException

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
from fts3rest.lib.middleware.fts3auth.authorization import authorize, authorized
from fts3rest.lib.middleware.fts3auth.constants import TRANSFER, PRIVATE, NONE, VO

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


def _get_job(job_id, env=None):
    job = Session.query(Job).get(job_id)
    if job is None:
        raise NotFound('No job with the id "%s" has been found' % job_id)
    if not authorized(
        TRANSFER, resource_owner=job.user_dn, resource_vo=job.vo_name, env=env
    ):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    return job


def get(job_list):
    """
    Get the job with the given ID
    """
    job_ids = job_list.split(",")
    multistatus = False

    # request is not available inside the generator
    environ = request.environ
    if "files" in request.args:
        file_fields = request.args["files"].split(",")
    else:
        file_fields = []

    statuses = []
    for job_id in filter(len, job_ids):
        try:
            job = _get_job(job_id, env=environ)
            if len(file_fields):

                class FileIterator(object):
                    def __init__(self, job_id):
                        self.job_id = job_id

                    def __call__(self):
                        for f in Session.query(File).filter(File.job_id == self.job_id):
                            fd = dict()
                            for field in file_fields:
                                try:
                                    fd[field] = getattr(f, field)
                                except AttributeError:
                                    pass
                            yield fd

                job.__dict__["files"] = FileIterator(job.job_id)()
            setattr(job, "http_status", "200 Ok")
            statuses.append(job)
        except HTTPException as ex:
            if len(job_ids) == 1:
                raise
            statuses.append(
                dict(
                    job_id=job_id,
                    http_status="%s %s" % (ex.code, ex.name),
                    http_message=ex.description,
                )
            )
            multistatus = True

    if len(job_ids) == 1:
        return statuses[0]

    if multistatus:
        return Response(statuses, status=207, mimetype="application/json")
    else:
        return jsonify(statuses)


def get_files(job_id):
    """
    Get the files within a job
    """
    owner = Session.query(Job.user_dn, Job.vo_name).filter(Job.job_id == job_id).first()
    if owner is None:
        raise NotFound('No job with the id "%s" has been found' % job_id)
    if not authorized(TRANSFER, resource_owner=owner[0], resource_vo=owner[1]):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    files = (
        Session.query(File).filter(File.job_id == job_id).options(noload(File.retries))
    )
    return Response(
        files.yield_per(100).enable_eagerloads(False), mimetype="application/json"
    )


def cancel_files(job_id, file_ids):
    """
    Cancel individual files - comma separated for multiple - within a job
    """
    job = _get_job(job_id)

    if job.job_type != "N":
        raise BadRequest(
            "Multihop or reuse jobs must be cancelled at once (%s)" % str(job.job_type)
        )

    file_ids = file_ids.split(",")
    changed_states = []

    try:
        # Mark files in the list as CANCELED
        for file_id in file_ids:
            file = Session.query(File).get(file_id)
            if not file or file.job_id != job_id:
                changed_states.append("File does not belong to the job")
                continue

            if file.file_state not in FileActiveStates:
                changed_states.append(file.file_state)
                continue

            file.file_state = "CANCELED"
            file.finish_time = datetime.utcnow()
            file.dest_surl_uuid = None
            changed_states.append("CANCELED")
            Session.merge(file)

        # Mark job depending on the status of the rest of files
        not_changed_states = [
            f.file_state for f in job.files if f.file_id not in file_ids
        ]
        all_states = not_changed_states + changed_states

        # All files within the job have been canceled
        if not not_changed_states:
            job.job_state = "CANCELED"
            job.cancel_job = True
            job.job_finished = datetime.utcnow()
            log.warning("Cancelling all remaining files within the job %s" % job_id)
        # No files in non-terminal, mark the job as CANCELED too
        elif not any(s for s in all_states if s in FileActiveStates):
            log.warning(
                "Cancelling a file within a job with others in terminal state (%s)"
                % job_id
            )
            job.job_state = "CANCELED"
            job.cancel_job = True
            job.job_finished = datetime.utcnow()
        else:
            log.warning(
                "Cancelling files within a job with others still active (%s)" % job_id
            )

        Session.merge(job)
        Session.commit()
    except Exception:
        Session.rollback()
        raise
    if len(changed_states) > 1:
        return jsonify(changed_states)
    else:
        return jsonify(changed_states[0])


def cancel_all_by_vo():
    raise NotFound


def cancel_all():
    raise NotFound


def get_file_retries(job_id, file_id):
    """
    Get the retries for a given file
    """
    owner = Session.query(Job.user_dn, Job.vo_name).filter(Job.job_id == job_id).all()
    if owner is None or len(owner) < 1:
        raise NotFound('No job with the id "%s" has been found' % job_id)
    if not authorized(TRANSFER, resource_owner=owner[0][0], resource_vo=owner[0][1]):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    f = Session.query(File.file_id).filter(File.file_id == file_id)
    if not f:
        raise NotFound('No file with the id "%d" has been found' % file_id)
    retries = Session.query(FileRetryLog).filter(FileRetryLog.file_id == file_id)
    return Response(retries.all(), mimetype="application/json")


def get_dm(job_id):
    """
    Get the data management tasks within a job
    """
    owner = Session.query(Job.user_dn, Job.vo_name).filter(Job.job_id == job_id).first()
    if owner is None:
        raise NotFound('No job with the id "%s" has been found' % job_id)
    if not authorized(TRANSFER, resource_owner=owner[0], resource_vo=owner[1]):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    dm = Session.query(DataManagement).filter(DataManagement.job_id == job_id)
    return Response(
        dm.yield_per(100).enable_eagerloads(False), mimetype="application/json"
    )


def get_field():
    raise NotFound


def cancel():
    raise NotFound


def modify():
    raise NotFound


def submit():
    raise NotFound
