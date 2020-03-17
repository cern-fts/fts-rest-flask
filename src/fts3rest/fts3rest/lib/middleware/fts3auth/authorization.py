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

import functools

from flask import request
from werkzeug.exceptions import Forbidden

from .constants import *


def authorized(operation, resource_owner=None, resource_vo=None, env=None):
    """
    Check if the user has enough privileges for a given operation

    Args:
        op:             The operation to perform
        resource_owner: Who owns the resource
        resource_vo:    VO of the owner of the resource
        env:            Environment (i.e. os.environ)

    Returns:
        True if the logged user has enough rights to perform the
        operation 'op' over a resource whose owner is resource_owner:resource_vo
    """
    if env is None:
        env = request.environ

    if not "fts3.User.Credentials" in env:
        return False

    user = env["fts3.User.Credentials"]
    granted_level = user.get_granted_level_for(operation)

    if granted_level == ALL:
        return True
    elif granted_level == VO:
        return (
            resource_vo is None
            or user.has_vo(resource_vo)
            or resource_owner == user.user_dn
        )
    elif granted_level == PRIVATE:
        return resource_owner is None or resource_owner == user.user_dn


def authorize(op, env=None):
    """
    Decorator to check if the user has enough privileges to perform a given operation

    Args:
        op: The required operation level

    Returns:
        A method that can be used to decorate the resource/method
    """

    def authorize_inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not authorized(op, env=env):
                raise Forbidden("Not enough permissions")
            return func(*args, **kwargs)

        return wrapper

    return authorize_inner


def require_certificate(func):
    """
    If the authentication method is not via certificate, deny access
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = request.environ["fts3.User.Credentials"]
        if user.method != "certificate":
            raise Forbidden("Certificate required")
        return func(*args, **kwargs)

    return wrapper
