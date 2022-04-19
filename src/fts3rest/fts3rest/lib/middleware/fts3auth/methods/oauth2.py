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

import types
import logging
from urllib.parse import urlparse
from fts3rest.lib.middleware.fts3auth.credentials import InvalidCredentials

log = logging.getLogger(__name__)


def _oauth2_get_granted_level_for(self, operation):
    # All users authenticated through IAM will be considered root users
    return "all"


def do_authentication(credentials, env, config):
    """
    The user will be the one who gave the bearer token
    """
    # TODO: There is a circular dependency between credentials::UserCredentials and
    #       oauth2provider::FTS3OAuth2ResourceProvider
    from fts3rest.lib.oauth2provider import FTS3OAuth2ResourceProvider

    res_provider = FTS3OAuth2ResourceProvider(env, config)
    authn = res_provider.get_authorization()
    if authn is None:
        return False
    if not authn.is_valid:
        if authn.error is not None:
            log.info("Raising invalid OAuth2 credentials")
            message = authn.error
            if authn.error == "access_denied":
                message = "Invalid OAuth2 credentials"
            raise InvalidCredentials(message)
        return False

    credentials.user_dn = authn.credentials.dn
    credentials.dn.append(authn.credentials.dn)
    _build_vo_from_token_auth(credentials, authn)
    credentials.delegation_id = authn.credentials.dlg_id
    credentials.method = "oauth2"

    # Override get_granted_level_for so we can filter by the scope
    setattr(credentials, "oauth2_scope", authn.scope)
    setattr(
        credentials,
        "get_granted_level_for_overriden",
        credentials.get_granted_level_for,
    )
    setattr(
        credentials,
        "get_granted_level_for",
        types.MethodType(_oauth2_get_granted_level_for, credentials),
    )
    return True


def _build_vo_from_token_auth(credentials, token_auth):
    if token_auth.groups is not None:
        for group in token_auth.groups:
            if group.startswith("/"):
                group = group[1:]
            if group not in credentials.vos:
                credentials.vos.append(group)
        credentials.voms_cred.extend(token_auth.groups)
    else:
        credentials.vos.append(_build_vo_from_issuer(token_auth.issuer))


def _build_vo_from_issuer(issuer):
    try:
        return urlparse(issuer).hostname
    except Exception:
        return issuer
