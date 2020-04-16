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

from werkzeug.exceptions import (
    NotFound,
    BadRequest,
    Forbidden,
    InternalServerError,
    ServiceUnavailable,
)
from flask import request
from datetime import datetime

import errno
import logging
import os
from stat import S_ISDIR
import tempfile
from urllib.parse import urlparse, unquote_plus


import json

from fts3.model import Credential
from fts3rest.model.meta import Session
from fts3rest.lib.http_exceptions import HTTPAuthenticationTimeout
from fts3rest.lib.gfal2_wrapper import Gfal2Wrapper, Gfal2Error
from fts3rest.lib.middleware.fts3auth.authorization import authorize
from fts3rest.lib.middleware.fts3auth.constants import DATAMANAGEMENT
from fts3rest.lib.helpers.jsonify import jsonify

log = logging.getLogger(__name__)

try:
    from fts3rest.controllers.CSdropbox import DropboxConnector

    dropbox_available = True
except ImportError as import_ex:
    dropbox_available = False
    log.warning(str(import_ex))


def _get_valid_surl():
    surl = request.values.get("surl")
    if not surl:
        raise BadRequest("Missing surl parameter")
    parsed = urlparse(surl)
    if parsed.scheme in ["file"]:
        raise BadRequest("Forbiden SURL scheme")
    return str(surl)


def _get_credentials():
    user = request.environ["fts3.User.Credentials"]
    cred = Session.query(Credential).get((user.delegation_id, user.user_dn))
    if not cred:
        raise HTTPAuthenticationTimeout("No delegated proxy available")

    if "oauth2" != user.method:
        if cred.termination_time <= datetime.utcnow():
            raise HTTPAuthenticationTimeout(
                "Delegated proxy expired (%s)" % user.delegation_id
            )

        tmp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pem", prefix="rest-proxy-", delete=False
        )
        tmp_file.write(cred.proxy)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        return tmp_file
    else:
        if cred.termination_time <= datetime.utcnow():
            raise HTTPAuthenticationTimeout(
                "Token with delegationId (%s), has expired" % user.delegation_id
            )
        return cred.proxy


def _http_status_from_errno(err_code):
    if err_code in (errno.EPERM, errno.EACCES):
        return Forbidden
    elif err_code == errno.ENOENT:
        return NotFound
    elif err_code in (errno.EAGAIN, errno.EBUSY, errno.ETIMEDOUT):
        return ServiceUnavailable
    elif err_code in (errno.ENOTDIR, errno.EPROTONOSUPPORT):
        return BadRequest
    else:
        return InternalServerError


def _http_error_from_gfal2_error(error):
    raise _http_status_from_errno(error.errno)("[%d] %s" % (error.errno, error.message))


def _is_dropbox(uri):
    return uri.startswith("dropbox") and dropbox_available


def _set_dropbox_headers(context):
    # getting the tokens and add them to the context
    user = request.environ["fts3.User.Credentials"]
    dropbox_con = DropboxConnector(user.user_dn, "dropbox")
    dropbox_info = dropbox_con._get_dropbox_info()
    dropbox_user_info = dropbox_con._get_dropbox_user_info()
    context.set_opt_string("DROPBOX", "APP_KEY", dropbox_info.app_key)
    context.set_opt_string("DROPBOX", "APP_SECRET", dropbox_info.app_secret)
    context.set_opt_string("DROPBOX", "ACCESS_TOKEN", dropbox_user_info.access_token)
    context.set_opt_string(
        "DROPBOX", "ACCESS_TOKEN_SECRET", dropbox_user_info.access_token_secret
    )
    return context


def _stat_impl(context, surl):
    st_stat = context.stat(surl)
    return {
        "mode": st_stat.st_mode,
        "nlink": st_stat.st_nlink,
        "size": st_stat.st_size,
        "atime": st_stat.st_atime,
        "mtime": st_stat.st_mtime,
        "ctime": st_stat.st_ctime,
    }


def _list_impl(context, surl):
    dir_handle = context.opendir(surl)
    listing = {}
    (entry, st_stat) = dir_handle.readpp()
    while entry:
        d_name = entry.d_name
        if S_ISDIR(st_stat.st_mode):
            d_name += "/"
        listing[d_name] = {
            "size": st_stat.st_size,
            "mode": st_stat.st_mode,
            "mtime": st_stat.st_mtime,
        }
        (entry, st_stat) = dir_handle.readpp()
    return listing


def _rename_impl(context, rename_dict):
    if len(rename_dict["old"]) == 0 or len(rename_dict["new"]) == 0:
        raise BadRequest("No old or name specified")

    old_path = rename_dict["old"]
    new_path = rename_dict["new"]

    if _is_dropbox(str(old_path)):
        context = _set_dropbox_headers(context)

    return context.rename(str(old_path), str(new_path))


def _unlink_impl(context, unlink_dict):
    if len(unlink_dict["surl"]) == 0:
        raise BadRequest('No parameter "surl" specified')

    path = unlink_dict["surl"]

    if _is_dropbox(str(path)):
        context = _set_dropbox_headers(context)

    return context.unlink(str(path))


def _rmdir_impl(context, rmdir_dict):
    if len(rmdir_dict["surl"]) == 0:
        raise BadRequest('No parameter "surl" specified')

    path = rmdir_dict["surl"]

    if _is_dropbox(str(path)):
        context = _set_dropbox_headers(context)

    return context.rmdir(str(path))


def _mkdir_impl(context, mkdir_dict):
    if len(mkdir_dict["surl"]) == 0:
        raise BadRequest('No parameter "surl" specified')

    path = mkdir_dict["surl"]

    if _is_dropbox(str(path)):
        context = _set_dropbox_headers(context)

    return context.mkdir(str(path), 0o775)


@authorize(DATAMANAGEMENT)
@jsonify
def list():
    """
    List the content of a remote directory
    """
    surl = _get_valid_surl()
    cred = _get_credentials()

    m = Gfal2Wrapper(cred, _list_impl)
    try:
        return m(surl)
    except Gfal2Error as ex:
        _http_error_from_gfal2_error(ex)
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            try:
                os.unlink(cred.name)
            except Exception:
                pass


@authorize(DATAMANAGEMENT)
@jsonify
def stat():
    """
    Stat a remote file
    """
    surl = _get_valid_surl()
    cred = _get_credentials()

    m = Gfal2Wrapper(cred, _stat_impl)
    try:
        return m(surl)
    except Gfal2Error as ex:
        _http_error_from_gfal2_error(ex)
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            os.unlink(cred.name)


@authorize(DATAMANAGEMENT)
@jsonify
def mkdir():
    """
    Create a remote file
    """
    cred = _get_credentials()

    try:
        if request.method == "POST":
            if request.content_type == "application/json":
                unencoded_body = request.data
            else:
                unencoded_body = unquote_plus(request.data)
        else:
            raise BadRequest("Unsupported method %s" % request.method)

        mkdir_dict = json.loads(unencoded_body)
        m = Gfal2Wrapper(cred, _mkdir_impl)
        try:
            return m(mkdir_dict)
        except Gfal2Error as ex:
            _http_error_from_gfal2_error(ex)
    except ValueError as ex:
        raise BadRequest("Invalid value within the request: %s" % str(ex))
    except TypeError as ex:
        raise BadRequest("Malformed request: %s" % str(ex))
    except KeyError as ex:
        raise BadRequest("Missing parameter: %s" % str(ex))
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            os.unlink(cred.name)


@authorize(DATAMANAGEMENT)
@jsonify
def unlink():
    """
    Remove a remote file
    """
    cred = _get_credentials()

    try:
        if request.method == "POST":
            if request.content_type == "application/json":
                unencoded_body = request.data
            else:
                unencoded_body = unquote_plus(request.data)
        else:
            raise BadRequest("Unsupported method %s" % request.method)

        unlink_dict = json.loads(unencoded_body)

        m = Gfal2Wrapper(cred, _unlink_impl)
        try:
            return m(unlink_dict)
        except Gfal2Error as ex:
            _http_error_from_gfal2_error(ex)

    except ValueError as ex:
        raise BadRequest("Invalid value within the request: %s" % str(ex))
    except TypeError as ex:
        raise BadRequest("Malformed request: %s" % str(ex))
    except KeyError as ex:
        raise BadRequest("Missing parameter: %s" % str(ex))
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            os.unlink(cred.name)


@authorize(DATAMANAGEMENT)
@jsonify
def rmdir():
    """
    Remove a remote folder
    """
    cred = _get_credentials()

    try:
        if request.method == "POST":
            if request.content_type == "application/json":
                unencoded_body = request.data
            else:
                unencoded_body = unquote_plus(request.data)
        else:
            raise BadRequest("Unsupported method %s" % request.method)

        rmdir_dict = json.loads(unencoded_body)

        m = Gfal2Wrapper(cred, _rmdir_impl)
        try:
            return m(rmdir_dict)
        except Gfal2Error as ex:
            _http_error_from_gfal2_error(ex)

    except ValueError as ex:
        raise BadRequest("Invalid value within the request: %s" % str(ex))
    except TypeError as ex:
        raise BadRequest("Malformed request: %s" % str(ex))
    except KeyError as ex:
        raise BadRequest("Missing parameter: %s" % str(ex))
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            os.unlink(cred.name)


@authorize(DATAMANAGEMENT)
@jsonify
def rename():
    """
    Stat a remote file
    """
    cred = _get_credentials()

    try:

        if request.method == "POST":
            if request.content_type == "application/json":
                unencoded_body = request.data
            else:
                unencoded_body = unquote_plus(request.data)
        else:
            raise BadRequest("Unsupported method %s" % request.method)

        rename_dict = json.loads(unencoded_body)

        m = Gfal2Wrapper(cred, _rename_impl)
        try:
            return m(rename_dict)
        except Gfal2Error as ex:
            _http_error_from_gfal2_error(ex)

    except ValueError as ex:
        raise BadRequest("Invalid value within the request: %s" % str(ex))
    except TypeError as ex:
        raise BadRequest("Malformed request: %s" % str(ex))
    except KeyError as ex:
        raise BadRequest("Missing parameter: %s" % str(ex))
    finally:
        # Delete the temp file if we are using a certificate based auth method
        if not isinstance(cred, str):
            os.unlink(cred.name)
