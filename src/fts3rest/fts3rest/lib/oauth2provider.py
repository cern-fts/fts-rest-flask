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

import logging
from datetime import datetime, timedelta
import json
import jwt
from fts3rest.model.meta import Session
from fts3rest.lib.middleware.fts3auth.constants import VALID_OPERATIONS
from fts3rest.lib.oauth2lib.provider import (
    AuthorizationProvider,
    ResourceAuthorization,
    ResourceProvider,
)
from fts3rest.lib.openidconnect import oidc_manager, jwt_options_unverified
from fts3rest.lib.middleware.fts3auth.methods import oauth2
from jwcrypto.jwk import JWK
from flask import request

from fts3rest.model import CredentialCache
from fts3rest.model.oauth2 import OAuth2Application, OAuth2Code, OAuth2Token

log = logging.getLogger(__name__)


class FTS3OAuth2AuthorizationProvider(AuthorizationProvider):
    """
    OAuth2 Authorization provider, specific methods
    """

    def validate_client_id(self, client_id):
        app = Session.query(OAuth2Application).get(client_id)
        return app is not None

    def validate_client_secret(self, client_id, client_secret):
        app = Session.query(OAuth2Application).get(client_id)
        if not app:
            return False
        return app.client_secret == client_secret

    def validate_scope(self, client_id, scope):
        app = Session.query(OAuth2Application).get(client_id)
        for s in scope:
            if s not in VALID_OPERATIONS or s not in app.scope:
                return False
        return True

    def validate_redirect_uri(self, client_id, redirect_uri):
        app = Session.query(OAuth2Application).get(client_id)
        if not app:
            return False
        return redirect_uri in app.redirect_to.split()

    def validate_access(self):
        user = request.environ["fts3.User.Credentials"]
        return user is not None

    def from_authorization_code(self, client_id, code, scope):
        code = Session.query(OAuth2Code).get(code)
        if not code:
            return None
        return {"dlg_id": code.dlg_id}

    def from_refresh_token(self, client_id, refresh_token, scope):
        code = Session.query(OAuth2Token).get((client_id, refresh_token))
        if not code:
            return None
        return {"dlg_id": code.dlg_id}

    def _insert_user(self, user):
        # We will need the user in t_credential_cache at least!
        cred = (
            Session.query(CredentialCache)
            .filter(CredentialCache.dlg_id == user.delegation_id)
            .first()
        )
        if not cred:
            cred = CredentialCache(
                dlg_id=user.delegation_id,
                dn=user.user_dn,
                cert_request=None,
                priv_key=None,
                voms_attrs="\n".join(user.voms_cred),
            )
            Session.merge(cred)

    def persist_authorization_code(self, client_id, code, scope):
        user = request.environ["fts3.User.Credentials"]
        self._insert_user(user)
        # Remove previous codes
        Session.query(OAuth2Code).filter(
            (OAuth2Code.client_id == client_id)
            & (OAuth2Code.dlg_id == user.delegation_id)
        ).delete()
        # Token
        code = OAuth2Code(
            client_id=client_id, code=code, scope=scope, dlg_id=user.delegation_id
        )
        Session.merge(code)
        Session.commit()

    def is_already_authorized(self, dlg_id, client_id, scope):
        code = Session.query(OAuth2Token).filter(
            (OAuth2Token.client_id == client_id) & (OAuth2Token.dlg_id == dlg_id)
        )
        if scope:
            code = code.filter(OAuth2Token.scope == scope)
        code = code.all()
        if len(code) > 0:
            return True
        else:
            return None

    def persist_token_information(
        self,
        client_id,
        scope,
        access_token,
        token_type,
        expires_in,
        refresh_token,
        data,
    ):
        # Remove previous tokens
        Session.query(OAuth2Token).filter(
            (OAuth2Token.dlg_id == data["dlg_id"])
            & (OAuth2Token.client_id == client_id)
        ).delete()
        # Add new
        token = OAuth2Token(
            client_id=client_id,
            scope=scope,
            access_token=access_token,
            token_type=token_type,
            expires=datetime.utcnow() + timedelta(seconds=expires_in),
            refresh_token=refresh_token,
            dlg_id=data["dlg_id"],
        )
        Session.merge(token)
        Session.commit()

    def discard_authorization_code(self, client_id, code):
        auth_code = Session.query(OAuth2Code).get(code)
        if auth_code is not None:
            Session.delete(auth_code)
            Session.commit()

    def discard_refresh_token(self, client_id, refresh_token):
        token = Session.query(OAuth2Token).get((client_id, refresh_token))
        if token is not None:
            Session.delete(token)
            Session.commit()


class FTS3ResourceAuthorization(ResourceAuthorization):
    dlg_id = None
    credentials = None
    subject = None
    issuer = None
    expiry = None
    scope = None
    groups = None
    wlcg_profile = False


class FTS3OAuth2ResourceProvider(ResourceProvider):
    """
    OAuth2 resource provider
    """

    def __init__(self, environ, config):
        self.environ = environ
        self.config = config

    @property
    def authorization_class(self):
        return FTS3ResourceAuthorization

    def get_authorization_header(self):
        return self.environ.get("HTTP_AUTHORIZATION", None)

    def obtain_refresh_token_from_auth(self, authorization):
        """
        Obtain a refresh token from a filled-in token authorization object

        :param authorization: the token authorization object as filled-in
                              by the validate_access_token() method
        :return: an access/refresh token pair
        """
        if authorization.issuer is None or authorization.token is None:
            raise ValueError("Invalid token authorization object!")

        audience = None
        # Hardcoded audience for WLCG tokens
        if authorization.wlcg_profile:
            audience = "https://wlcg.cern.ch/jwt/v1/any"

        (access_token, refresh_token) = oidc_manager.generate_refresh_token(
            issuer=authorization.issuer,
            token=authorization.token,
            audience=audience,
            scope=authorization.scope,
        )
        return access_token, refresh_token

    def validate_access_token(self, access_token, authorization):
        """
        Validate access token offline or online

        Description of the algorithm:
          - Check whether the Token Issuer is supported
          - Validate access token offline (using cached keys) or online (using introspection RFC 7662)
            -- Offline validation must have valid "exp", "iat" and "nbf" claims
            -- Online validation must include "offline_access" scope

        :param access_token:
        :param authorization: attribute to fill-in with token information
        """
        authorization.is_valid = False
        validation_method = "offline" if self._should_validate_offline() else "online"

        try:
            if not oidc_manager.token_issuer_supported(access_token):
                authorization.error = "TokenProvider not supported"
                return
        except Exception as ex:
            log.warning("Exception during TokenProvider check: {}".format(ex))
            authorization.error = str(ex)
            return

        try:
            if validation_method == "offline":
                valid, credential = self._validate_token_offline(access_token)
            else:
                valid, credential = self._validate_token_online(access_token)
            if not valid:
                return
        except Exception as ex:
            log.warning(
                "Exception during {} validation: {}".format(validation_method, ex)
            )
            authorization.error = str(ex)
            return

        # Try to obtain scopes via best-effort introspection
        scope = self._scope_from_credential(credential)
        if scope is None:
            try:
                log.debug(
                    "Retrieving scopes via introspection: {}".format(credential["iss"])
                )
                response = oidc_manager.introspect(credential["iss"], access_token)
                scope = self._scope_from_credential(response)
            except Exception as ex:
                log.info("Exception retrieving scopes via introspection: {}".format(ex))
                pass

        authorization.is_oauth = True
        authorization.issuer = credential["iss"]
        authorization.subject = credential["sub"]
        authorization.client_id = credential.get("client_id")
        authorization.expiry = credential["exp"]
        authorization.scope = scope
        authorization.groups = credential.get("wlcg.groups")
        authorization.wlcg_profile = "wlcg.ver" in credential
        authorization.token = access_token
        authorization.expires_in = (
            datetime.utcfromtimestamp(credential["exp"]) - datetime.utcnow()
        )
        authorization.is_valid = authorization.expires_in > timedelta(seconds=0)

    def _validate_token_offline(self, access_token):
        return oauth2.validate_token_offline(access_token)

    def _validate_token_online(self, access_token):
        return oauth2.validate_token_online(access_token)

    def _scope_from_credential(self, credential):
        scope = credential.get("scope")
        if isinstance(scope, str):
            scope = scope.split()
        if isinstance(scope, list):
            scope.sort()
        return scope

    def _should_validate_offline(self):
        return self.config.get("fts3.ValidateAccessTokenOffline", True)
