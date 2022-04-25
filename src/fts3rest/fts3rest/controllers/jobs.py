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

from flask import request, Response
from werkzeug.exceptions import Forbidden, BadRequest, NotFound, Conflict

from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import noload

import logging

from fts3rest.model import Job, File, JobActiveStates, FileActiveStates
from fts3rest.model import DataManagement, DataManagementActiveStates
from fts3rest.model import Credential, FileRetryLog
from fts3rest.model import CloudStorage, CloudStorageUser, CloudCredentialCache
from fts3rest.model.meta import Session

from fts3rest.lib import swiftauth
from fts3rest.lib.http_exceptions import *
from fts3rest.lib.middleware.fts3auth.authorization import authorized, authorize
from fts3rest.lib.middleware.fts3auth.constants import TRANSFER, PRIVATE, NONE, VO
from fts3rest.lib.helpers.misc import get_input_as_dict
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.lib.helpers.msgbus import submit_state_change
from fts3rest.lib.JobBuilder import JobBuilder

log = logging.getLogger(__name__)

"""
Operations on jobs and transfers
"""


@authorize(TRANSFER)
@jsonify
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
    if filter_limit is not None and (filter_limit < 0 or filter_limit > 500):
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
        return jobs


def _get_job(job_id, env=None):
    job = Session.query(Job).get(job_id)
    if job is None:
        raise NotFound('No job with the id "%s" has been found' % job_id)
    if not authorized(
        TRANSFER, resource_owner=job.user_dn, resource_vo=job.vo_name, env=env
    ):
        raise Forbidden('Not enough permissions to check the job "%s"' % job_id)
    return job


@jsonify
def get(job_list):
    """
    Get the job with the given ID
    """
    job_ids = job_list.split(",")
    status_error_count = 0

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
            statuses.append(
                dict(
                    job_id=job_id,
                    http_status="%s %s" % (ex.code, ex.name),
                    http_message=ex.description,
                )
            )
            status_error_count += 1

    if len(job_ids) == 1:
        res = statuses[0]
        if status_error_count == 1:
            res = Response(
                statuses[0],
                status=statuses[0].get("http_status"),
                mimetype="application/json",
            )
    elif status_error_count > 0:
        res = Response(statuses, status=207, mimetype="application/json")
    else:
        res = statuses
    return res


@jsonify
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


@jsonify
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
        return changed_states
    else:
        return changed_states[0]


@jsonify
def cancel_all_by_vo(vo_name):
    """
    Cancel all files by the given vo_name
    """
    user = request.environ["fts3.User.Credentials"]

    now = datetime.utcnow()
    if not user.is_root:
        raise Forbidden("User does not have root privileges")

    try:
        # FTS3 daemon expects finish_time to be NULL in order to trigger the signal
        # to fts_url_copy
        file_count = (
            Session.query(File)
            .filter(File.vo_name == vo_name)
            .filter(File.file_state.in_(FileActiveStates))
            .update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "dest_surl_uuid": None,
                    "finish_time": None,
                },
                synchronize_session=False,
            )
        )

        # However, for data management operations there is nothing to signal, so
        # set job_finished
        dm_count = (
            Session.query(DataManagement)
            .filter(DataManagement.vo_name == vo_name)
            .filter(DataManagement.file_state.in_(DataManagementActiveStates))
            .update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "job_finished": now,
                    "finish_time": now,
                },
                synchronize_session=False,
            )
        )

        job_count = (
            Session.query(Job)
            .filter(Job.vo_name == vo_name)
            .filter(Job.job_state.in_(JobActiveStates))
            .update(
                {
                    "job_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "job_finished": now,
                },
                synchronize_session=False,
            )
        )
        Session.commit()
        Session.expire_all()
        log.info("Active jobs for VO %s canceled" % vo_name)
    except Exception:
        Session.rollback()
        raise
    return {
        "affected_files": file_count,
        "affected_dm": dm_count,
        "affected_jobs": job_count,
    }


@jsonify
def cancel_all():
    """
    Cancel all files
    """
    user = request.environ["fts3.User.Credentials"]

    now = datetime.utcnow()
    if not user.is_root:
        raise Forbidden("User does not have root privileges")

    try:
        # FTS3 daemon expects finish_time to be NULL in order to trigger the signal
        # to fts_url_copy
        file_count = (
            Session.query(File)
            .filter(File.file_state.in_(FileActiveStates))
            .update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "dest_surl_uuid": None,
                    "finish_time": None,
                },
                synchronize_session=False,
            )
        )

        # However, for data management operations there is nothing to signal, so
        # set job_finished
        dm_count = (
            Session.query(DataManagement)
            .filter(DataManagement.file_state.in_(DataManagementActiveStates))
            .update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "job_finished": now,
                    "finish_time": now,
                },
                synchronize_session=False,
            )
        )

        job_count = (
            Session.query(Job)
            .filter(Job.job_state.in_(JobActiveStates))
            .update(
                {
                    "job_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "job_finished": now,
                },
                synchronize_session=False,
            )
        )
        Session.commit()
        Session.expire_all()
        log.info("Active jobs canceled")
    except Exception:
        Session.rollback()
        raise

    return {
        "affected_files": file_count,
        "affected_dm": dm_count,
        "affected_jobs": job_count,
    }


@jsonify
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


@jsonify
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


@jsonify
def get_field(job_id, field):
    """
    Get a specific field from the job identified by id
    """
    job = _get_job(job_id)
    if hasattr(job, field):
        return getattr(job, field)
    else:
        raise NotFound("No such field")


def _multistatus(responses, expecting_multistatus=False):
    """
    Return 200 if everything is Ok, 207 if there is any errors,
    and, if input was only one, do not return an array
    """
    if not expecting_multistatus:
        single = responses[0]
        if isinstance(single, Job):
            if single.http_status not in ("200 Ok", "304 Not Modified"):
                return Response(
                    single, status=single.http_status, mimetype="application/json"
                )
        elif single["http_status"] not in ("200 Ok", "304 Not Modified"):
            return Response(
                single, status=single["http_status"], mimetype="application/json"
            )
        return single

    for response in responses:
        if isinstance(response, dict) and not response.get(
            "http_status", ""
        ).startswith("2"):
            return Response(responses, status=207, mimetype="application/json")
    return responses


@jsonify
def cancel(job_id_list):
    """
    Cancel the given job

    Returns the canceled job with its current status. CANCELED if it was canceled,
    its final status otherwise
    """
    requested_job_ids = job_id_list.split(",")
    cancellable_jobs = []
    responses = []

    # First, check which job ids exist and can be accessed
    for job_id in requested_job_ids:
        # Skip empty
        if not job_id:
            continue
        try:
            job = _get_job(job_id)
            if job.job_state in JobActiveStates:
                cancellable_jobs.append(job)
            else:
                setattr(job, "http_status", "304 Not Modified")
                setattr(job, "http_message", "The job is in a terminal state")
                log.warning(
                    "The job %s can not be canceled, since it is %s"
                    % (job_id, job.job_state)
                )
                responses.append(job)
        except HTTPException as ex:
            responses.append(
                dict(
                    job_id=job_id,
                    http_status="%s %s" % (ex.code, ex.name),
                    http_message=ex.description,
                )
            )

    # Now, cancel those that can be canceled
    now = datetime.utcnow()
    try:
        for job in cancellable_jobs:
            job.job_state = "CANCELED"
            job.cancel_job = True
            job.job_finished = now
            job.reason = "Job canceled by the user"

            # FTS3 daemon expects finish_time to be NULL in order to trigger the signal
            # to fts_url_copy, but this only makes sense if pid is set
            Session.query(File).filter(File.job_id == job.job_id).filter(
                File.file_state.in_(FileActiveStates), File.pid != None
            ).update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "dest_surl_uuid": None,
                    "finish_time": None,
                },
                synchronize_session=False,
            )
            Session.query(File).filter(File.job_id == job.job_id).filter(
                File.file_state.in_(FileActiveStates), File.pid == None
            ).update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "dest_surl_uuid": None,
                    "finish_time": now,
                },
                synchronize_session=False,
            )
            # However, for data management operations there is nothing to signal, so
            # set job_finished
            Session.query(DataManagement).filter(
                DataManagement.job_id == job.job_id
            ).filter(DataManagement.file_state.in_(DataManagementActiveStates)).update(
                {
                    "file_state": "CANCELED",
                    "reason": "Job canceled by the user",
                    "job_finished": now,
                    "finish_time": now,
                },
                synchronize_session=False,
            )
            job = Session.merge(job)

            log.info("Job %s canceled" % job.job_id)
            setattr(job, "http_status", "200 Ok")
            setattr(job, "http_message", None)
            responses.append(job)
            Session.expunge(job)
        Session.commit()
        Session.expire_all()
    except Exception:
        Session.rollback()
        raise

    return _multistatus(responses, expecting_multistatus=len(requested_job_ids) > 1)


@jsonify
def modify(job_id_list):
    """
    Modify a job, or set of jobs
    """
    requested_job_ids = job_id_list.split(",")
    modifiable_jobs = []
    responses = []

    # First, check which job ids exist and can be accessed
    for job_id in requested_job_ids:
        # Skip empty
        if not job_id:
            continue
        try:
            job = _get_job(job_id)
            if job.job_state in JobActiveStates:
                modifiable_jobs.append(job)
            else:
                setattr(job, "http_status", "304 Not Modified")
                setattr(job, "http_message", "The job is in a terminal state")
                log.warning(
                    "The job %s can not be modified, since it is %s"
                    % (job_id, job.job_state)
                )
                responses.append(job)
        except HTTPException as ex:
            responses.append(
                dict(
                    job_id=job_id,
                    http_status="%s %s" % (ex.code, ex.name),
                    http_message=ex.description,
                )
            )

    # Now, modify those that can be
    modification = get_input_as_dict(request)
    priority = None
    # todo: verify this is correct for the migration
    try:
        priority = int(modification["params"]["priority"])
    except KeyError:
        pass
    except ValueError:
        raise BadRequest("Invalid priority value")

    try:
        for job in modifiable_jobs:
            if priority:
                for file in job.files:
                    file.priority = priority
                    Session.merge(file)
                    log.info(
                        "File from Job %s priority changed to %d"
                        % (job.job_id, priority)
                    )
                job.priority = priority
                job = Session.merge(job)
                log.info("Job %s priority changed to %d" % (job.job_id, priority))
            setattr(job, "http_status", "200 Ok")
            setattr(job, "http_message", None)
            responses.append(job)
            Session.expunge(job)
        Session.commit()
        Session.expire_all()
    except Exception:
        Session.rollback()
        raise

    return _multistatus(responses, expecting_multistatus=len(requested_job_ids) > 1)


def _set_swift_credentials(se_url, user_dn, access_token, os_project_id, os_tokens):
    """
    Retrieve and save OS token for accessing Swift object store
    """
    storage_name = 'SWIFT:' + se_url[se_url.rfind('/') + 1:]
    cloud_storage = Session.query(CloudStorage).get(storage_name)
    if not swiftauth.verified_swift_storage_user(user_dn, storage_name):
        raise BadRequest(
            "Cloud user is not registered for using cloud storage %s"
            % storage_name
        )

    if cloud_storage:
        # handling manually set OS tokens (takes precedence)
        if os_tokens and os_project_id in os_tokens:
            cloud_credential = swiftauth.set_swift_credential_cache(dict(),
                                                                    user_dn,
                                                                    storage_name,
                                                                    os_tokens[os_project_id],
                                                                    os_project_id)
        # fetch OS token using OIDC access token
        elif access_token:
            cloud_credential = swiftauth.get_os_token(user_dn, access_token,
                                                      cloud_storage, os_project_id)
        # return if no OS token and OIDC token provided
        else:
            log.info(
                "No cloud credential %s for storage %s provided"
                % (user_dn, storage_name)
            )
            return
        # save swift credentials
        log.debug("cloud credential string: %s" % str(cloud_credential))
        if cloud_credential:
            if not swiftauth.verified_swift_project_user(cloud_storage, cloud_credential):
                raise BadRequest(
                    "Cloud user does not have access to the required Swift project"
                )
            try:
                Session.merge(CloudCredentialCache(**cloud_credential))
                Session.commit()
            except Exception as ex:
                log.debug(
                    "Failed to save credentials for dn: %s because: %s"
                    % (user_dn, str(ex))
                )
                Session.rollback()
    else:
        log.info(
            "Error retrieving cloud credential %s for storage %s"
            % (user_dn, storage_name)
        )


def _initialize_swift_cred(proxy, ids, method):
    access_token = None
    if method == 'oauth2':
        access_token = proxy[:proxy.find(':')]
    try:
        os_project_ids = ids.split(':')
    except AttributeError:
        raise BadRequest(
            "No OS project id is provided for the Swift transfer"
        )
    return access_token, os_project_ids


@authorize(TRANSFER)
@jsonify
def submit():
    """
    Submits a new job

    It returns the information about the new submitted job. To know the format for the
    submission, /api-docs/schema/submit gives the expected format encoded as a JSON-schema.
    It can be used to validate (i.e in Python, jsonschema.validate)
    """
    log.debug("submitting job")
    # First, the request has to be valid JSON
    submitted_dict = get_input_as_dict(request)

    # The auto-generated delegation id must be valid
    user = request.environ["fts3.User.Credentials"]
    credential = Session.query(Credential).get((user.delegation_id, user.user_dn))
    if credential is None:
        raise HTTPAuthenticationTimeout('No delegation found for "%s"' % user.user_dn)
    if credential.expired():
        remaining = credential.remaining()
        seconds = abs(remaining.seconds + remaining.days * 24 * 3600)
        raise HTTPAuthenticationTimeout(
            "The delegated credentials expired %d seconds ago (%s)"
            % (seconds, user.delegation_id)
        )
    if user.method != "oauth2" and credential.remaining() < timedelta(hours=1):
        raise HTTPAuthenticationTimeout(
            "The delegated credentials has less than one hour left (%s)"
            % user.delegation_id
        )

    # Populate the job and files
    populated = JobBuilder(user, **submitted_dict)

    log.info("%s (%s) is submitting a transfer job" % (user.user_dn, user.vos[0]))

    # Exchange access token for OS token(s) for swift stores
    swift_source = populated.job['source_se'].startswith('swift')
    swift_dest = populated.job['dest_se'].startswith('swift')
    if swift_source or swift_dest:
        access_token, os_project_ids = _initialize_swift_cred(credential.proxy,
                                                              populated.job['os_project_id'],
                                                              user.method)
        id_cnt = 0
        if swift_source:
            _set_swift_credentials(populated.job['source_se'], user.user_dn, access_token,
                                   os_project_ids[id_cnt], populated.params['os_token'])
            id_cnt += 1
        if swift_dest:
            if id_cnt == 1 and len(os_project_ids) < 2:
                raise BadRequest(
                    "Only one OS project id is provided for the Swift to Swift transfer"
                )
            _set_swift_credentials(populated.job['dest_se'], user.user_dn, access_token,
                                   os_project_ids[id_cnt], populated.params['os_token'])

    # Insert the job
    try:
        try:
            Session.execute(Job.__table__.insert(), [populated.job])
        except IntegrityError:
            raise Conflict("The sid provided by the user is duplicated")
        if len(populated.files):
            Session.execute(File.__table__.insert(), populated.files)
        if len(populated.datamanagement):
            Session.execute(DataManagement.__table__.insert(), populated.datamanagement)
        Session.flush()
        Session.commit()
    except IntegrityError as err:
        Session.rollback()
        raise Conflict("The submission is duplicated " + str(err))
    except Exception:
        Session.rollback()
        raise

    # Send messages
    # Need to re-query so we get the file ids
    job = Session.query(Job).get(populated.job_id)
    for i in range(len(job.files)):
        try:
            submit_state_change(job, job.files[i], populated.files[0]["file_state"])
        except Exception as ex:
            log.warning("Failed to write state message to disk: %s" % str(ex))

    if len(populated.files):
        log.info(
            "Job %s submitted with %d transfers"
            % (populated.job_id, len(populated.files))
        )
    elif len(populated.datamanagement):
        log.info(
            "Job %s submitted with %d data management operations"
            % (populated.job_id, len(populated.datamanagement))
        )

    return {"job_id": populated.job_id}
