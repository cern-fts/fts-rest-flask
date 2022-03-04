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


from werkzeug.exceptions import NotFound, BadRequest, Forbidden
from flask import request
import urllib
import logging
import json
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen
from urllib.error import HTTPError
from fts3rest.lib import swiftauth
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.model.meta import Session
from fts3rest.model import CloudStorage, CloudStorageUser, CloudCredentialCache
from fts3rest.controllers.CSInterface import Connector

log = logging.getLogger(__name__)


class SwiftConnector(Connector):

    def is_registered(self):
        pass

    def remove_token(self):
        pass

    def get_access_requested(self):
        pass

    def is_access_requested(self):
        pass

    def get_access_granted(self):
        pass

    def get_folder_content(self):
        surl, project_id, access_token = self._get_valid_surl()
        return self._get_content(surl, project_id, access_token)

    def get_file_link(self, path):
        # "dropbox" could be also "sandbox"
        pass

    # Internal functions

    def _get_content(self, surl, project_id, access_token):
        parsed = urlparse(surl)
        urlbase = "https://" + parsed.hostname + "/v1/AUTH_" + project_id
        params = None
        rightmost_slash = parsed.path.rfind("/")
        if rightmost_slash != 0:
            params = "prefix=" + parsed.path[rightmost_slash+1:] + "/&delimiter=/"
            url = urlbase + parsed.path[:rightmost_slash]
        else:
            url = urlbase + parsed.path
        return self._make_call(
            url,
            self._get_swift_token(parsed.hostname, project_id, access_token),
            params,
        )

    def _get_valid_surl(self):
        surl = request.args.get("surl")
        project_id = request.args.get("projectid")
        try:
            access_token = request.headers.get("Authorization").split()[1]
        except Exception as ex:
            access_token = None
        if not surl:
            raise BadRequest("Missing surl parameter")
        parsed = urlparse(surl)
        if parsed.scheme in ["file"]:
            raise BadRequest("Forbiden SURL scheme")
        if not project_id:
            raise BadRequest("Missing project id parameter")
        return str(surl), str(project_id), access_token

    def _get_swift_token(self, storage_name, project_id, access_token):
        try:
            Session.query(CloudStorageUser).filter_by(
                user_dn=self.user_dn,
                storage_name='SWIFT:' + storage_name
            ).first()
        except Exception as ex:
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

    def _make_call(self, command_url, os_token, parameters):
        if parameters is not None:
            command_url += "?" + parameters
        headers = {"X-Auth-Token": os_token, "Accept": "application/json"}

        try:
            req = urllib.request.Request(url=command_url, headers=headers, method="GET")
            response = urllib.request.urlopen(req)
            res_con = response.read()
            return res_con
        except HTTPError as e:
            return str(e.code) + str(e.read())
