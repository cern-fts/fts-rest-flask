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


from werkzeug.exceptions import BadRequest, InternalServerError
from flask import request
import urllib
import logging
import json
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import HTTPError
from fts3rest.lib import swiftauth
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.model.meta import Session
from fts3rest.model import CloudStorage, CloudStorageUser, CloudCredentialCache
from fts3rest.controllers.CSInterface import Connector

log = logging.getLogger(__name__)


class SwiftConnector(Connector):
    @jsonify
    def is_registered(self):
        surl = request.args.get("surl")
        parsed = urlparse(surl)
        if swiftauth.verified_swift_storage_user(self.user_dn, 'SWIFT:' + parsed.hostname):
            return True
        return False

    def remove_token(self):
        pass

    def get_access_requested(self):
        pass

    def is_access_requested(self):
        pass

    def get_access_granted(self):
        cred = self._get_valid_creds()
        if not cred["os_token"]:
            raise BadRequest(
                "No OS token provided."
            )
        return self._set_os_token(cred)

    def get_folder_content(self):
        cred = self._get_valid_creds()
        return self._get_content(cred)

    def get_file_link(self, path):
        pass

    # Internal functions

    def _get_content(self, cred):
        parsed = urlparse(cred["surl"])
        urlbase = "https://" + parsed.hostname + "/v1/AUTH_" + cred["project_id"]
        params = None
        rightmost_slash = parsed.path.rfind("/")
        if rightmost_slash != 0:
            params = "prefix=" + parsed.path[rightmost_slash+1:] + "/&delimiter=/"
            url = urlbase + parsed.path[:rightmost_slash]
        else:
            url = urlbase + parsed.path
        return self._make_call(
            url,
            cred["os_token"] if cred["os_token"]
            else self._get_swift_token(parsed.hostname, cred["project_id"], cred["access_token"]),
            params,
        )

    def _get_valid_creds(self):
        cred = dict()
        cred["surl"] = str(request.args.get("surl"))
        cred["project_id"] = str(request.args.get("projectid"))

        try:
            cred["access_token"] = request.headers.get("Authorization").split()[1]
        except Exception as ex:
            cred["access_token"] = None

        try:
            cred["os_token"] = request.headers.get("X-Auth-Token")
        except Exception as ex:
            cred["os_token"] = None

        if not cred["surl"]:
            raise BadRequest("Missing surl parameter")
        parsed = urlparse(cred["surl"])
        if parsed.scheme in ["file"]:
            raise BadRequest("Forbiden SURL scheme")
        if not cred["project_id"]:
            raise BadRequest("Missing project id parameter")

        return cred

    def _get_swift_token(self, storage_name, project_id, access_token):
        if not swiftauth.verified_swift_storage_user(self.user_dn, 'SWIFT:' + storage_name):
            raise BadRequest(
                "Cloud user is not registered for using cloud storage %s"
                % storage_name
            )

        cloud_credential = None
        if access_token:
            # try to fetch an OS token with an OIDC token and save it
            try:
                cloud_storage = Session.query(CloudStorage).get('SWIFT:' + storage_name)
                cloud_credential = swiftauth.get_os_token(self.user_dn, access_token,
                                      cloud_storage, project_id)
                if cloud_credential:
                    try:
                        Session.merge(CloudCredentialCache(**cloud_credential))
                        Session.commit()
                    except Exception as ex:
                        log.debug(
                            "Failed to save credentials for dn: %s because: %s"
                            % (self.user_dn, str(ex))
                        )
                        Session.rollback()
                    return cloud_credential["os_token"]
            except Exception as ex:
                log.debug("failed to retrieve an OS token")
        # try to fetch OS token stored in DB
        if not cloud_credential:
            credential_cache = (
                Session.query(CloudCredentialCache)
                    .get({"os_project_id": project_id,
                          "user_dn": self.user_dn,
                          "storage_name": 'SWIFT:' + storage_name})
            )
            if credential_cache:
                return credential_cache.os_token
        raise BadRequest("Do not have enough credentials to access cloud storage")

    def _set_os_token(self, cred):
        parsed = urlparse(cred["surl"])
        if not swiftauth.verified_swift_storage_user(self.user_dn, 'SWIFT:' + parsed.hostname):
            raise BadRequest(
                "Cloud user is not registered for using cloud storage %s"
                % parsed.hostname
            )

        cloud_credential = swiftauth.set_swift_credential_cache(dict(),
                                                                self.user_dn,
                                                                'SWIFT:' + parsed.hostname,
                                                                cred["os_token"],
                                                                cred["project_id"])
        if cloud_credential:
            try:
                Session.merge(CloudCredentialCache(**cloud_credential))
                Session.commit()
            except Exception as ex:
                log.debug(
                    "Failed to save credentials for dn: %s because: %s"
                    % (self.user_dn, str(ex))
                )
                Session.rollback()
                raise InternalServerError(
                    "Error when saving credentials"
                )
        else:
            raise InternalServerError(
                "Error when saving credentials"
            )
        return {}

    def _make_call(self, command_url, os_token, params):
        if params is not None:
            command_url += "?" + params
        headers = {"X-Auth-Token": os_token, "Accept": "application/json"}

        try:
            req = urllib.request.Request(url=command_url, headers=headers, method="GET")
            response = urllib.request.urlopen(req)
            res_con = response.read()
            return res_con
        except HTTPError as e:
            return str(e.code) + str(e.read())
