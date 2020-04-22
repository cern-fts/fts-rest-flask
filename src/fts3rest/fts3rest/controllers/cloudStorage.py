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


from flask import request, Blueprint
from .CSInterface import CSInterface
from werkzeug.exceptions import Unauthorized

"""
Cloud storage support
"""


def _before():
    user = request.environ["fts3.User.Credentials"]
    if user.method == "unauthenticated":
        raise Unauthorized


cstorage_blueprint = Blueprint("cstorage_blueprint", __name__)
cstorage_blueprint.before_request(_before)


def _get_user_dn():
    user = request.environ["fts3.User.Credentials"]
    return user.user_dn


def is_registered(self, service):
    """
    Return a boolean indicating if the user has a token registered
    for the given certificate
    """
    controller = CSInterface(self._get_user_dn(), service)
    return controller.is_registered()


def remove_token(service, start_response):
    """
    Remove the token associated with the given service
    """
    controller = CSInterface(_get_user_dn(), service)
    controller.remove_token()
    start_response("204 No Content", [])
    return [""]


def get_access_requested(service):
    """
    First authorization step: obtain a request token
    """
    controller = CSInterface(_get_user_dn(), service)
    return controller.get_access_requested()


def is_access_requested(service):
    """
    Returns the status of the authorization
    """
    controller = CSInterface(_get_user_dn(), service)
    return controller.is_access_requested()


def get_access_granted(service):
    """
    Third authorization step: get a valid access token
    """
    controller = CSInterface(_get_user_dn(), service)
    return controller.get_access_granted()


def get_folder_content(service):
    """
    Get the content of the given directory
    """
    controller = CSInterface(_get_user_dn(), service)
    return controller.get_folder_content()


def get_file_link(service, file_path):
    """
    Get the final HTTP url from the logical file_path inside the cloud storage
    """
    controller = CSInterface(_get_user_dn(), service)
    return controller.get_file_link(file_path)
