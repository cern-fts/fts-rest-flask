"""
This module contains methods for JobBuilder.
Originally these methods were in the JobBuilder module, but they were separated to
reduce the complexity of the module.
"""
import logging
import random
import uuid
import json
from flask import current_app as app
from werkzeug.exceptions import BadRequest, Forbidden, InternalServerError

from fts3rest.model import BannedSE
from fts3rest.model.meta import Session

from fts3rest.lib.scheduler.schd import Scheduler
from fts3rest.lib.scheduler.db import Database
from fts3rest.lib.scheduler.Cache import ThreadLocalCache

log = logging.getLogger(__name__)

BASE_ID = uuid.UUID("urn:uuid:01874efb-4735-4595-bc9c-591aef8240c9")

DEFAULT_PARAMS = {
    "bring_online": -1,
    "archive_timeout": -1,
    "verify_checksum": False,
    "copy_pin_lifetime": -1,
    "gridftp": "",
    "job_metadata": None,
    "overwrite": False,
    "overwrite_on_retry": False,
    "overwrite_hop": False,
    "dst_file_report": False,
    "reuse": None,
    "multihop": False,
    "source_spacetoken": "",
    "spacetoken": "",
    "retry": 0,
    "retry_delay": 0,
    "priority": 3,
    "max_time_in_queue": 0,
    "s3alternate": False,
}


def get_base_id():
    return BASE_ID


def get_vo_id(vo_name):
    log.debug("VO name: " + vo_name)
    return uuid.uuid5(BASE_ID, vo_name)


def get_storage_element(uri):
    """
    Returns the storage element of the given uri, which is the scheme +
    hostname without the port

    Args:
        uri: An urlparse instance
    """
    return "%s://%s" % (uri.scheme, uri.hostname)


def is_dest_surl_uuid_enabled(vo_name):
    """
    Returns True if the given vo_name allows dest_surl_uuid.

    Args:
        vo_name: Name of the vo
    """
    list_of_vos = app.config.get("fts3.CheckDuplicates", "None")
    if not list_of_vos:
        return False
    if vo_name in list_of_vos or "*" in list_of_vos:
        return True
    return False


def validate_url(url):
    """
    Validates the format and content of the url
    """
    if not url.scheme:
        raise ValueError("Missing scheme (%s)" % url.geturl())
    if url.scheme == "file":
        raise ValueError("Can not transfer local files (%s)" % url.geturl())
    if not url.path or (url.path == "/" and not url.query):
        raise ValueError("Missing path (%s)" % url.geturl())
    if not url.hostname:
        raise ValueError("Missing host (%s)" % url.geturl())


def validate_staging_metadata(metadata):
    if isinstance(metadata, dict):
        return metadata
    try:
        return json.loads(metadata)
    except:
        raise ValueError("Staging metadata not in JSON format")


def metadata(data):
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except:
        return {"label": str(data)}


def safe_flag(flag):
    """
    Traduces from different representations of flag values to True/False
    True/False => True/False
    1/0 => True/False
    'Y'/'N' => True/False
    """
    if isinstance(flag, str):
        return len(flag) > 0 and flag[0].upper() == "Y"
    else:
        return bool(flag)


def safe_filesize(size):
    if isinstance(size, float):
        return size
    elif size is None:
        return 0.0
    else:
        return float(size)


def safe_int(param, default=-1):
    """
    Checks if param is of type int
    If it is not, try to convert it
    If it fails, make it default
    """
    if isinstance(param, int):
        return param
    else:
        try:
            return int(param)
        except:
            return default


def generate_hashed_id():
    """
    Generates a uniformly distributed value between 0 and 2**16
    This is intended to split evenly the load across node
    The name is an unfortunately legacy from when this used to
    be based on a hash on the job
    """
    return random.randint(0, (2**16) - 1)  # nosec


def has_multiple_options(files):
    """
    Returns a tuple (Boolean, Integer)
    Boolean is True if there are multiple replica entries, and Integer
    holds the number of unique files.
    """
    ids = [f["file_index"] for f in files]
    id_count = len(ids)
    unique_id_count = len(set(ids))
    return unique_id_count != id_count, unique_id_count


def select_best_replica(files, vo_name, entry_state, strategy):

    dst = files[0]["dest_se"]
    activity = files[0]["activity"]
    user_filesize = files[0]["user_filesize"]

    queue_provider = Database(Session)
    cache_provider = ThreadLocalCache(queue_provider)
    # s = Scheduler(queue_provider)
    s = Scheduler(cache_provider)
    source_se_list = map(lambda f: f["source_se"], files)

    if strategy == "orderly":
        sorted_ses = source_se_list

    elif strategy == "queue" or strategy == "auto":
        sorted_ses = map(lambda x: x[0], s.rank_submitted(source_se_list, dst, vo_name))

    elif strategy == "success":
        sorted_ses = map(lambda x: x[0], s.rank_success_rate(source_se_list, dst))

    elif strategy == "throughput":
        sorted_ses = map(lambda x: x[0], s.rank_throughput(source_se_list, dst))

    elif strategy == "file-throughput":
        sorted_ses = map(
            lambda x: x[0], s.rank_per_file_throughput(source_se_list, dst)
        )

    elif strategy == "pending-data":
        sorted_ses = map(
            lambda x: x[0], s.rank_pending_data(source_se_list, dst, vo_name, activity)
        )

    elif strategy == "waiting-time":
        sorted_ses = map(
            lambda x: x[0], s.rank_waiting_time(source_se_list, dst, vo_name, activity)
        )

    elif strategy == "waiting-time-with-error":
        sorted_ses = map(
            lambda x: x[0],
            s.rank_waiting_time_with_error(source_se_list, dst, vo_name, activity),
        )

    elif strategy == "duration":
        sorted_ses = map(
            lambda x: x[0],
            s.rank_finish_time(source_se_list, dst, vo_name, activity, user_filesize),
        )
    else:
        raise BadRequest(strategy + " algorithm is not supported by Scheduler")

    # We got the storages sorted from better to worst following
    # the chosen strategy.
    # We need to find the file with the source matching that best_se
    best_index = 0
    best_se = next(sorted_ses)
    for index, transfer in enumerate(files):
        if transfer["source_se"] == best_se:
            best_index = index
            break

    files[best_index]["file_state"] = entry_state
    if is_dest_surl_uuid_enabled(vo_name):
        files[best_index]["dest_surl_uuid"] = str(
            uuid.uuid5(BASE_ID, files[best_index]["dest_surl"].encode("utf-8"))
        )


def apply_banning(files):
    """
    Query the banning information for all pairs, reject the job
    as soon as one SE can not submit.
    Update wait_timeout and wait_timestamp is there is a hit
    """
    # Usually, banned SES will be in the order of ~100 max
    # Files may be several thousands
    # We get all banned in memory so we avoid querying too many times the DB
    # We then build a dictionary to make look up easy
    banned_ses = dict()
    for b in Session.query(BannedSE):
        banned_ses[str(b.se)] = (b.vo, b.status)

    for f in files:
        source_banned = banned_ses.get(str(f["source_se"]), None)
        dest_banned = banned_ses.get(str(f["dest_se"]), None)
        banned = False

        if source_banned and (
            source_banned[0] == f["vo_name"] or source_banned[0] == "*"
        ):
            if source_banned[1] != "WAIT_AS":
                raise Forbidden("%s is banned" % f["source_se"])
            banned = True

        if dest_banned and (dest_banned[0] == f["vo_name"] or dest_banned[0] == "*"):
            if dest_banned[1] != "WAIT_AS":
                raise Forbidden("%s is banned" % f["dest_se"])
            banned = True

        if banned:
            if f["file_state"] == "SUBMITTED":
                f["file_state"] = "ON_HOLD"
            elif f["file_state"] == "STAGING":
                f["file_state"] = "ON_HOLD_STAGING"
            elif f["file_state"] == "DELETE":
                continue
            else:
                InternalServerError("Unexpected initial state: %s" % f["file_state"])


def seconds_from_value(value):
    """
    Transform an interval value to seconds
    If value is an integer, assume it is hours (backwards compatibility)
    Otherwise, look at the suffix
    """
    if isinstance(value, int) and value != 0:
        return value * 3600
    elif not isinstance(value, str):
        return None

    try:
        suffix = value[-1].lower()
        value = value[:-1]
        if suffix == "s":
            return int(value)
        elif suffix == "m":
            return int(value) * 60
        elif suffix == "h":
            return int(value) * 3600
        elif suffix == "d":
            return int(value) * 3600 * 24
        else:
            return None
    except Exception:
        return None
