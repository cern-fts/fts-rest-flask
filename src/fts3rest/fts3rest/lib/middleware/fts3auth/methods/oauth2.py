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
from datetime import datetime
from fts3rest.lib.middleware.fts3auth.credentials import (
    generate_delegation_id,
    InvalidCredentials,
)
from fts3rest.model.meta import Session
from fts3rest.model import Credential

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

    credentials.method = "oauth2"
    credentials.user_dn = authn.subject
    credentials.dn.append(authn.subject)
    _build_vo_from_token_auth(credentials, authn)
    credentials.delegation_id = generate_delegation_id(
        credentials.user_dn, credentials.voms_cred
    )

    # Extend UserCredentials object with OAuth2 specific fields
    setattr(credentials, "oauth2_scope", " ".join(authn.scope) if authn.scope else None)
    setattr(credentials, "wlcg_profile", authn.wlcg_profile)

    # Override get_granted_level_for to allow filtering by scope claim
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
    else:
        credentials.vos.append(_build_vo_from_issuer(token_auth.issuer))
    if token_auth.scope is not None:
        credentials.voms_cred.extend(token_auth.scope)


def _build_vo_from_issuer(issuer):
    try:
        return urlparse(issuer).hostname
    except Exception:
        return issuer


def _handle_credential_storing(resource_provider, credentials, token_auth):
    """
    This method takes care of all database token-related operations.

    Ideally, the token credentials would only touch the database
    during the delegation process. However, as delegation is not
    implemented yet for tokens, it happens on every authentication.

    Algorithm:
        - If a credential already exists in the database but has expired, delete it
        - If there's no credential anymore, exchange the access token for a refresh token
        - Store the access/refresh token pair in the database

    :param resource_provider: the OAuth2 Resource Provider object
    :param credentials: the constructed UserCredential object
    :param token_auth: the token authorization object
    """
    # Check if a credential already exists in the database
    credential_db = (
        Session.query(Credential)
        .filter(Credential.dlg_id == credentials.delegation_id)
        .first()
    )
    # Delete expired credential
    if credential_db and credential_db.expired():
        log.info(
            "Deleting expired credential dlg_id={}".format(credentials.delegation_id)
        )
        try:
            Session.delete(credential_db)
            Session.commit()
        except Exception as ex:
            log.warning("Failed to delete expired credentials: {}".format(ex))
            Session.rollback()
        credential_db = None
    if not credential_db:
        # Exchange access token for a refresh token if no credential exists
        log.debug("Obtaining refresh token")
        access_token, refresh_token = resource_provider.obtain_refresh_token_from_auth(
            token_auth
        )
        # Store access/refresh token pair in the database
        credential = Credential(
            dlg_id=credentials.delegation_id,
            dn=credentials.user_dn,
            proxy=str(access_token) + ":" + str(refresh_token),
            voms_attrs=" ".join(credentials.voms_cred)
            if len(credentials.voms_cred) > 0
            else "",
            termination_time=datetime.utcfromtimestamp(token_auth.expiry),
        )
        try:
            Session.merge(credential)
            Session.commit()
        except Exception:
            Session.rollback()
            raise
