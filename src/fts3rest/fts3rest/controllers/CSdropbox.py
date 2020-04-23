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

# Based on https://www.dropbox.com/developers/core/docs

from werkzeug.exceptions import NotFound, BadRequest, Forbidden
from flask import request
import urllib
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from fts3rest.lib.helpers.jsonify import jsonify
from fts3rest.model.meta import Session
from fts3.model import CloudStorage, CloudStorageUser
from fts3rest.controllers.CSInterface import Connector

dropboxEndpoint = "https://www.dropbox.com"
dropboxApiEndpoint = "https://api.dropbox.com"


class DropboxConnector(Connector):
    @jsonify
    def is_registered(self):
        info = self._get_dropbox_user_info()
        if info:
            return info.is_registered()
        else:
            return False

    def get_access_requested(self):
        dropbox_info = self._get_dropbox_info()
        request_tokens = self._make_call(
            dropboxApiEndpoint + "/1/oauth/request_token",
            'OAuth oauth_version="1.0", oauth_signature_method="PLAINTEXT",'
            'oauth_consumer_key="'
            + dropbox_info.app_key
            + '", oauth_signature="'
            + dropbox_info.app_secret
            + '&"',
            None,
        )

        # It returns: oauth_token_secret=b9q1n5il4lcc&oauth_token=mh7an9dkrg59
        tokens = request_tokens.split("&")
        newuser = CloudStorageUser(
            user_dn=self.user_dn,
            storage_name=dropbox_info.storage_name,
            request_token=tokens[1].split("=")[1],
            request_token_secret=tokens[0].split("=")[1],
            vo_name="",
        )
        try:
            Session.add(newuser)
            Session.commit()
        except Exception:
            Session.rollback()
            raise

        return request_tokens

    @jsonify
    def is_access_requested(self):
        info = self._get_dropbox_user_info()
        if info is None:
            raise NotFound(
                'No registered user for the service "%s" has been found' % self.service
            )

        if info.is_registered():
            res = self._get_content("/")
            if res.startswith("401"):
                try:
                    Session.delete(info)
                    Session.commit()
                except:
                    Session.rollback()
                    raise
                raise NotFound(
                    'No registered user for the service "%s" has been found'
                    % self.service
                )

        return info.storage_name

    def remove_token(self):
        info = self._get_dropbox_user_info()
        if info is None:
            raise NotFound(
                'No registered user for the service "%s" has been found' % self.service
            )
        try:
            Session.delete(info)
            Session.commit()
        except:
            Session.rollback()
            raise

    def get_access_granted(self):
        dropbox_user_info = self._get_dropbox_user_info()
        if not dropbox_user_info:
            raise BadRequest(
                'No registered user for the service "%s" has been found' % self.service
            )

        dropbox_info = self._get_dropbox_info()
        if not dropbox_info:
            raise NotFound("Dropbox info not found in the database")

        access_tokens = self._make_call(
            dropboxApiEndpoint + "/1/oauth/access_token",
            'OAuth oauth_version="1.0", oauth_signature_method="PLAINTEXT", oauth_consumer_key="'
            + dropbox_info.app_key
            + '", oauth_token="'
            + dropbox_user_info.request_token
            + '", oauth_signature="'
            + dropbox_info.app_secret
            + "&"
            + dropbox_user_info.request_token_secret
            + '"',
            None,
        )

        # It returns: oauth_token=<access-token>&oauth_token_secret=<access-token-secret>&uid=<user-id>
        ret = access_tokens
        access_tokens = access_tokens.split("&")
        dropbox_user_info.access_token = access_tokens[1].split("=")[1]
        dropbox_user_info.access_token_secret = access_tokens[0].split("=")[1]
        try:
            Session.add(dropbox_user_info)
            Session.commit()
        except Exception:
            Session.rollback()
            raise

        return ret

    def get_folder_content(self):
        surl = self._get_valid_surl()
        return self._get_content(surl)

    def _get_content(self, surl):
        return self._make_call(
            dropboxApiEndpoint + "/1/metadata/dropbox" + surl,
            self._get_auth_key(),
            "list=true",
        )

    def get_file_link(self, path):
        # "dropbox" could be also "sandbox"
        return self._make_call(
            dropboxApiEndpoint + "/1/media/dropbox/" + path, self._get_auth_key(), ""
        )

    # Internal functions

    def _get_dropbox_user_info(self):
        dropbox_user_info = Session.query(CloudStorageUser).get(
            (self.user_dn, self.service, "")
        )
        return dropbox_user_info

    def _get_valid_surl(self):
        surl = request.params.get("surl")
        if not surl:
            raise BadRequest("Missing surl parameter")
        parsed = urlparse(surl)
        if parsed.scheme in ["file"]:
            raise BadRequest("Forbiden SURL scheme")
        return str(surl)

    def _get_dropbox_info(self):
        dropbox_info = Session.query(CloudStorage).get(self.service)
        if dropbox_info is None:
            raise Forbidden(
                "No registration information found for the service %s" % self.service
            )
        return dropbox_info

    def _get_auth_key(self):
        dropbox_user_info = self._get_dropbox_user_info()
        dropbox_info = self._get_dropbox_info()
        return (
            'OAuth oauth_version="1.0", oauth_signature_method="PLAINTEXT",'
            'oauth_consumer_key="'
            + dropbox_info.app_key
            + '", oauth_token="'
            + dropbox_user_info.access_token
            + ', oauth_signature="'
            + dropbox_info.app_secret
            + "&"
            + dropbox_user_info.access_token_secret
            + '"'
        )

    def _make_call(self, command_url, auth_headers, parameters):
        if parameters is not None:
            command_url += "?" + parameters
        headers = {"Authorization": auth_headers}
        values = {}

        try:
            data = urlencode(values)
            req = urllib.request.Request(command_url, data, headers)
            response = urllib.request.urlopen(req)
            res_con = response.read()
            return res_con
        except HTTPError as e:
            return str(e.code) + str(e.read())
