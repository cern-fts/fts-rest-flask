#   Copyright 2014-2020 CERN
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
from werkzeug.exceptions import NotFound, BadRequest, Conflict
from fts3rest.controllers.config import audit_configuration
from flask import request, Response
import json
import logging
from datetime import datetime
from sqlalchemy import distinct, func, and_

from fts3.model import BannedDN, BannedSE, Job, File, JobActiveStates, FileActiveStates
from fts3rest.model.meta import Session
from fts3rest.lib.http_exceptions import *
from fts3rest.lib.middleware.fts3auth.authorization import authorize
from fts3rest.lib.middleware.fts3auth.constants import *
from fts3rest.lib.helpers.jsonify import jsonify

log = logging.getLogger(__name__)


def _ban_se(storage, vo_name, allow_submit, status, message):
    """
    Mark in the db the given storage as banned
    """
    user = request.environ["fts3.User.Credentials"]
    banned = BannedSE()
    banned.se = storage
    banned.addition_time = datetime.utcnow()
    banned.admin_dn = user.user_dn
    banned.vo = vo_name
    banned.message = message
    if allow_submit and status == "WAIT":
        banned.status = "WAIT_AS"
    else:
        banned.status = status
    try:
        Session.merge(banned)
        Session.commit()
    except Exception:
        Session.rollback()
        raise


def _ban_dn(dn, message):
    """
    Mark in the db the given DN as banned
    """
    user = request.environ["fts3.User.Credentials"]
    banned = BannedDN()
    banned.dn = dn
    banned.addition_time = datetime.utcnow()
    banned.admin_dn = user.user_dn
    banned.message = message
    try:
        Session.merge(banned)
        Session.commit()
    except Exception:
        Session.rollback()
        raise


def _cancel_transfers(storage=None, vo_name=None):
    """
    Cancels the transfers that have the given storage either in source or destination,
    and belong to the given VO.
    Returns the list of affected jobs ids.
    """
    affected_job_ids = set()
    files = Session.query(File.file_id).filter(
        and_(
            (File.source_se == storage) | (File.dest_se == storage),
            File.file_state.in_(FileActiveStates + ["NOT_USED"]),
        )
    )
    if vo_name and vo_name != "*":
        files = files.filter(File.vo_name == vo_name)

    now = datetime.utcnow()

    try:
        for row in files:
            file_id = row[0]
            job_id, file_index = (
                Session.query(File.job_id, File.file_index)
                .filter(File.file_id == file_id)
                .one()
            )
            affected_job_ids.add(job_id)
            # Cancel the affected file
            Session.query(File).filter(File.file_id == file_id).update(
                {
                    "file_state": "CANCELED",
                    "reason": "Storage banned",
                    "finish_time": now,
                    "dest_surl_uuid": None,
                },
                synchronize_session=False,
            )
            # If there are alternatives, enable them
            if Session.bind.dialect.name == "mysql":
                limit = " LIMIT 1"
            else:
                limit = ""
            Session.execute(
                "UPDATE t_file SET"
                "   file_state = 'SUBMITTED' "
                "WHERE"
                "  job_id = :job_id AND file_index = :file_index AND file_state = 'NOT_USED' "
                + limit,
                dict(job_id=job_id, file_index=file_index),
            )

        Session.commit()
        Session.expire_all()
    except Exception:
        Session.rollback()
        raise

    # Set each job terminal state if needed
    try:
        for job_id in affected_job_ids:
            n_files = (
                Session.query(func.count(distinct(File.file_id)))
                .filter(File.job_id == job_id)
                .all()[0][0]
            )
            n_canceled = (
                Session.query(func.count(distinct(File.file_id)))
                .filter(File.job_id == job_id)
                .filter(File.file_state == "CANCELED")
                .all()[0][0]
            )
            n_finished = (
                Session.query(func.count(distinct(File.file_id)))
                .filter(File.job_id == job_id)
                .filter(File.file_state == "FINISHED")
                .all()[0][0]
            )
            n_failed = (
                Session.query(func.count(distinct(File.file_id)))
                .filter(File.job_id == job_id)
                .filter(File.file_state == "FAILED")
                .all()[0][0]
            )

            n_terminal = n_canceled + n_finished + n_failed

            # Job finished!
            if n_terminal == n_files:
                reason = None
                Session.query(Job).filter(Job.job_id == job_id).update(
                    {"job_state": "CANCELED", "job_finished": now, "reason": reason}
                )

        Session.commit()
    except Exception:
        Session.rollback()
        raise
    return affected_job_ids


def _cancel_jobs(dn):
    """
    Cancel all jobs that belong to dn.
    Returns the list of affected jobs ids.
    """
    jobs = Session.query(Job.job_id).filter(
        Job.job_state.in_(JobActiveStates), Job.user_dn == dn, Job.job_finished == None
    )
    job_ids = [j[0] for j in jobs]

    try:
        now = datetime.utcnow()
        for job_id in job_ids:
            Session.query(File).filter(File.job_id == job_id).filter(
                File.file_state.in_(FileActiveStates)
            ).update(
                {"file_state": "CANCELED", "reason": "User banned", "finish_time": now},
                synchronize_session=False,
            )
            Session.query(Job).filter(Job.job_id == job_id).update(
                {"job_state": "CANCELED", "reason": "User banned", "job_finished": now},
                synchronize_session=False,
            )
        Session.commit()
        Session.expire_all()
        return job_ids
    except Exception:
        Session.rollback()
        raise


def _set_to_wait_helper(storage, vo_name, from_state, to_state):
    """
    Helper for _set_to_wait
    """
    file_ids = Session.query(File.file_id).filter(
        and_(File.file_state == from_state),
        (File.source_se == storage) | (File.dest_se == storage),
    )
    if vo_name and vo_name != "*":
        file_ids = file_ids.filter(File.vo_name == vo_name)

    file_ids = map(lambda j: j[0], file_ids.all())
    job_ids = set()
    for file_id in file_ids:
        Session.query(File).filter(File.file_id == file_id).update(
            {"file_state": to_state}, synchronize_session=False
        )
        job_ids.add(Session.query(File).get(file_id).job_id)
    return job_ids


def _set_to_wait(storage, vo_name):
    """
    Updates the transfers that have the given storage either in source or destination,
    and belong to the given VO.
    """
    try:
        job_ids = _set_to_wait_helper(storage, vo_name, "SUBMITTED", "ON_HOLD")
        job_ids.update(
            _set_to_wait_helper(storage, vo_name, "STAGING", "ON_HOLD_STAGING")
        )
        Session.commit()
        Session.expire_all()
    except Exception:
        Session.rollback()
        raise
    return job_ids


def _reenter_queue(storage, vo_name):
    """
    Resets to SUBMITTED or STAGING those transfers that were set ON_HOLD with a previous banning
    Returns the list of affects job ids.
    """
    job_ids = (
        Session.query(distinct(File.job_id))
        .filter((File.source_se == storage) | (File.dest_se == storage))
        .filter(File.file_state.in_(["ON_HOLD", "ON_HOLD_STAGING"]))
    )
    if vo_name and vo_name != "*":
        job_ids = job_ids.filter(File.vo_name == vo_name)
    job_ids = map(lambda j: j[0], job_ids.all())

    try:
        for job_id in job_ids:
            Session.query(File).filter(
                File.job_id == job_id, File.file_state == "ON_HOLD_STAGING"
            ).update({"file_state": "STAGING"}, synchronize_session=False)
            Session.query(File).filter(
                File.job_id == job_id, File.file_state == "ON_HOLD"
            ).update({"file_state": "SUBMITTED"}, synchronize_session=False)
    except Exception:
        Session.rollback()
        raise

    return job_ids


@authorize(CONFIG)
@jsonify
def ban_se():
    """
    Ban a storage element. Returns affected jobs ids.
    """
    if request.content_type == "application/json":
        try:
            input_dict = json.loads(request.data)
        except Exception:
            raise BadRequest("Malformed input")
    else:
        input_dict = request.values

    storage = input_dict.get("storage", None)
    if not storage:
        raise BadRequest("Missing storage parameter")

    user = request.environ["fts3.User.Credentials"]
    vo_name = user.vos[0]
    allow_submit = bool(input_dict.get("allow_submit", False))
    status = input_dict.get("status", "cancel").upper()

    if status not in ["CANCEL", "WAIT"]:
        raise BadRequest("status can only be cancel or wait")

    if allow_submit and status == "CANCEL":
        raise BadRequest("allow_submit and status = CANCEL can not be combined")

    _ban_se(storage, vo_name, allow_submit, status, input_dict.get("message", ""))
    audit_configuration(
        "ban-se", "Storage %s for %s banned (%s)" % (storage, vo_name, status)
    )

    if status == "CANCEL":
        affected = _cancel_transfers(storage=storage, vo_name=vo_name)
    else:
        affected = _set_to_wait(storage=storage, vo_name=vo_name)

    log.warning(
        "Storage %s banned (%s), %d jobs affected" % (storage, status, len(affected))
    )
    return affected


@authorize(CONFIG)
@jsonify
def unban_se():
    """
    Unban a storage element
    """
    storage = request.values.get("storage", None)
    if not storage:
        raise BadRequest("Missing storage parameter")
    job_ids = []
    try:
        user = request.environ["fts3.User.Credentials"]
        vo_name = user.vos[0]
        Session.query(BannedSE).filter(
            BannedSE.se == storage, BannedSE.vo == vo_name
        ).delete()
        job_ids = _reenter_queue(storage, vo_name)
        Session.commit()
    except Exception:
        Session.rollback()
        raise BadRequest("Storage not found")
    log.warning("Storage %s unbanned" % storage)
    audit_configuration("unban-se", "Storage %s unbanned" % storage)
    return Response([], status=204, mimetype="application/json")


@authorize(CONFIG)
@jsonify
def list_banned_se():
    """
    List banned storage elements
    """
    return Response(Session.query(BannedSE).all(), mimetype="application/json")


@authorize(CONFIG)
@jsonify
def ban_dn():
    """
    Ban a user
    """
    if request.content_type == "application/json":
        try:
            input_dict = json.loads(request.data)
        except Exception:
            raise BadRequest("Malformed input")
    else:
        input_dict = request.values

    user = request.environ["fts3.User.Credentials"]
    dn = input_dict.get("user_dn", None)

    if not dn:
        raise BadRequest("Missing dn parameter")
    if dn == user.user_dn:
        raise Conflict("The user tried to ban (her|his)self")

    _ban_dn(dn, input_dict.get("message", ""))
    affected = _cancel_jobs(dn=dn)

    audit_configuration("ban-dn", "User %s banned" % dn)
    log.warning("User %s banned, %d jobs affected" % (dn, len(list(affected))))

    return affected


@authorize(CONFIG)
def unban_dn():
    """
    Unban a user
    """
    dn = request.values.get("user_dn", None)
    if not dn:
        raise BadRequest("Missing user_dn parameter")

    banned = Session.query(BannedDN).get(dn)
    if banned:
        try:

            Session.delete(banned)
            Session.commit()
        except Exception:
            Session.rollback()
        log.warning("User %s unbanned" % dn)
    else:
        log.warning("Unban of user %s without effect" % dn)

    audit_configuration("unban-dn", "User %s unbanned" % dn)
    return Response([], status=204, mimetype="application/json")


@authorize(CONFIG)
@jsonify
def list_banned_dn():
    """
    List banned users
    """
    return Response(Session.query(BannedDN).all(), mimetype="application/json")
