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

import logging
import json
import jwt
import types

from urllib.parse import urlparse
from datetime import datetime
from fts3rest.lib.middleware.fts3auth.credentials import (
    generate_token_delegation_id,
    gridmap_vo,
    InvalidCredentials,
)
from fts3rest.lib.openidconnect import oidc_manager, jwt_options_unverified
from fts3rest.model.meta import Session
from fts3rest.model import Credential
from jwcrypto.jwk import JWK

log = logging.getLogger(__name__)


def validate_token_offline(access_token, audience=None):
    """
    Validate access token using cached information from the provider
    When enabled checks if access_token has the right audience

    :param access_token
    :param audience
    :return: tuple(valid, credential) or tuple(False, None)
    :raise Exception: exception on invalid token
    """

    def _decode(key):
        log.debug("Attempt decoding using key={}".format(key.export()))
        try:
            return jwt.decode(
                access_token,
                key.export_to_pem(),
                algorithms=[algorithm],
                options={"verify_aud": False},
            )
        except Exception:
            return None

    # Check the token has valid "exp", "iat" and "nbf" claims
    options = {"verify_exp": True, "verify_nbf": True, "verify_iat": True}
    if audience:
        # Verify that audience matches the expected
        options["verify_aud"] = True

    unverified_payload = jwt.decode(
        access_token,
        options=jwt_options_unverified(options),
        audience=audience,
    )
    unverified_header = jwt.get_unverified_header(access_token)
    issuer = unverified_payload["iss"]
    key_id = unverified_header.get("kid")
    algorithm = unverified_header.get("alg")
    log.debug("issuer={}, key_id={}, alg={}".format(issuer, key_id, algorithm))

    # Find the first key which decodes the token
    keys = oidc_manager.filter_provider_keys(issuer, key_id, algorithm)
    jwkeys = [JWK.from_json(json.dumps(key.to_dict())) for key in keys]
    for jwkey in jwkeys:
        credential = _decode(jwkey)
        if credential is not None:
            log.debug("offline_response::: {}".format(credential))
            return True, credential
    log.warning("No key managed to decode the token")
    return False, None


def validate_token_online(access_token, audience=None):
    """
    Validate access token using Introspection (RFC 7662).
    Furthermore, run some FTS specific validations, such as
    requiring the "offline_access" scope and requiring the right audience

    :param access_token:
    :param audience:
    :return: tuple(valid, credential) or tuple(False, None)
    :raise Exception: exception during introspection
           or if missing "offline_access" scope
    """
    options = {}
    if audience:
        options["verify_aud"] = True

    unverified_payload = jwt.decode(
        access_token, options=jwt_options_unverified(options), audience=audience
    )
    issuer = unverified_payload["iss"]
    log.debug("issuer={}".format(issuer))
    credential = oidc_manager.introspect(issuer, access_token)
    log.debug("online_response::: {}".format(credential))
    if not credential["active"]:
        return False, None
    # Perform FTS specific validations
    scopes = credential.get("scope")
    if scopes is None:
        raise ValueError("Scope claim not found in online validation response")
    if "offline_access" not in scopes:
        raise ValueError("Scope claim dos not contain offline_access")
    return True, credential


def _oauth2_get_granted_level_for(self, operation):
    # All users authenticated through IAM will be considered root users
    return "all"


def _get_vo_from_config(config, issuer):
    """
    Searches the specified FTS configuration for the VO for the specified
    issuer.

    :returns the VO or None if one not found
    """
    providers = config.get("fts3.Providers", None)
    if not providers:
        return None

    provider = config["fts3.Providers"].get(issuer, None)
    if not provider:
        return None

    vo = provider.get("vo", None)
    if not vo:
        return None

    return vo


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
    if authn.issuer is None or authn.subject is None:
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

    vo = gridmap_vo(credentials.user_dn)
    if vo:
        credentials.vos.append(vo)
    else:
        vo = _get_vo_from_config(config, authn.issuer)
        if vo:
            credentials.vos.append(vo)
        else:
            _build_vo_from_token_auth(credentials, authn)

    credentials.delegation_id = generate_token_delegation_id(
        authn.issuer, authn.subject
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
