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
from fts3rest.lib.middleware.fts3auth.credentials import generate_delegation_id
from fts3rest.lib.oauth2lib.provider import (
    AuthorizationProvider,
    ResourceAuthorization,
    ResourceProvider,
)
from fts3rest.lib.openidconnect import oidc_manager, jwt_options_unverified
from jwcrypto.jwk import JWK
from flask import request

from fts3rest.model import Credential, CredentialCache
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
    scope = None


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

    def validate_access_token(self, access_token, authorization):
        """
        Validate access token offline or online

        Description of the algorithm:
        - Validate access token offline (using cached keys) or online (using introspection RFC 7662).
        - Perform token credential post-validation
        - If a credential already exists in the DB and has not expired, the new token is discarded and the old
        credential is used.
        - If a credential already exists in the DB but has expired, delete it.
        - If there's no credential, Introspect the token to get additional information (if not done before). Then,
        exchange the access token with a refresh token. Store both tokens in the DB.

        :param access_token:
        :param authorization: attribute .is_valid is set to True if validation successful
        """
        authorization.is_valid = False
        validation_method = "offline" if self._should_validate_offline() else "online"

        try:
            if not oidc_manager.token_issuer_supported(access_token):
                authorization.error = "TokenProvider not supported"
                return
        except Exception as ex:
            log.warning("Exception during TokenProvider check: {}".format(str(ex)))
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
                "Exception during {} validation: {}".format(validation_method, str(ex))
            )
            authorization.error = str(ex)
            return

        # Check if a credential already exists in the DB
        credential_db = (
            Session.query(Credential).filter(Credential.dn == credential["sub"]).first()
        )
        if credential_db and credential_db.expired():
            log.debug("Deleting expired credential '{}'".format(credential["sub"]))
            Session.delete(credential_db)
            Session.commit()
            credential_db = None

        if not credential_db:
            if validation_method == "offline":
                log.debug("offline and not in db")
                # Introspect to obtain additional information
                try:
                    valid, credential = self._validate_token_online(access_token)
                    if not valid:
                        return
                except Exception as ex:
                    log.warning(
                        "Exception during online validation: {}".format(str(ex))
                    )
                    authorization.error = str(ex)
                    return
            # Store credential in DB
            log.debug("Store credential in DB")
            dlg_id = generate_delegation_id(credential["sub"], "")
            try:
                if "wlcg" in credential["iss"]:
                    # Hardcoded scope and audience for wlcg tokens. To change once the wlcg standard evolves
                    scope = "offline_access openid storage.read:/ storage.modify:/ wlcg.groups"
                    audience = "https://wlcg.cern.ch/jwt/v1/any"
                    (
                        access_token,
                        refresh_token,
                    ) = oidc_manager.generate_token_with_scope(
                        credential["iss"], access_token, scope, audience
                    )
                else:
                    refresh_token = oidc_manager.generate_refresh_token(
                        credential["iss"], access_token
                    )
            except Exception as ex:
                authorization.error = str(ex)
                return
            credential_db = self._save_credential(
                dlg_id,
                credential["sub"],
                str(access_token) + ":" + str(refresh_token),
                self._generate_voms_attrs(credential),
                datetime.utcfromtimestamp(credential["exp"]),
            )

        authorization.is_oauth = True
        authorization.token = credential_db.proxy.split(":")[0]
        authorization.dlg_id = credential_db.dlg_id
        authorization.expires_in = credential_db.termination_time - datetime.utcnow()
        if authorization.expires_in > timedelta(seconds=0):
            authorization.credentials = self._get_credentials(credential_db.dlg_id)
            if authorization.credentials:
                authorization.is_valid = True

    def _get_credentials(self, dlg_id):
        """
        Get the user credentials bound to the authorization token
        """
        return Session.query(Credential).filter(Credential.dlg_id == dlg_id).first()

    def _generate_voms_attrs(self, credential):
        attrs = [
            credential.get("email"),
            credential.get("username")
            or credential.get("user_id")
            or credential.get("client_id"),
        ]

        voms_attrs = " ".join(filter(None, attrs))
        log.debug("voms_attrs::: {}".format(voms_attrs))
        return voms_attrs

    def _validate_token_offline(self, access_token):
        """
        Validate access token using cached information from the provider
        :param access_token:
        :return: tuple(valid, credential) or tuple(False, None)
        :raise Exception: exception on invalid token
        """

        def _decode(key):
            log.debug("Attempt decoding using key={}".format(key.export()))
            try:
                audience = None
                options = {"verify_aud": False}
                # Check audience only for WLCG tokens
                if "wlcg" in issuer:
                    audience = "https://wlcg.cern.ch/jwt/v1/any"
                    options["verify_aud"] = True
                return jwt.decode(
                    access_token,
                    key.export_to_pem(),
                    algorithms=[algorithm],
                    audience=audience,
                    options=options,
                )
            except Exception:
                return None

        unverified_payload = jwt.decode(
            access_token,
            options=jwt_options_unverified(
                {"verify_exp": True, "verify_nbf": True, "verify_iat": True}
            ),
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

    def _validate_token_online(self, access_token):
        """
        Validate access token using Introspection (RFC 7662).
        Furthermore, run some FTS specific validations, such as
        requiring the "offline_access" scope.
        :param access_token:
        :return: tuple(valid, credential) or tuple(False, None)
        :raise Exception: exception during introspection
               or if missing "offline_access" scope
        """
        unverified_payload = jwt.decode(access_token, options=jwt_options_unverified())
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
            raise ValueError("Scope claim dos not contain 'offline_access'")
        return True, credential

    def _save_credential(self, dlg_id, dn, proxy, voms_attrs, termination_time):
        credential = Credential(
            dlg_id=dlg_id,
            dn=dn,
            proxy=proxy,
            voms_attrs=voms_attrs,
            termination_time=termination_time,
        )
        Session.add(credential)
        Session.commit()
        return credential

    def _should_validate_offline(self):
        return self.config.get("fts3.ValidateAccessTokenOffline", True)
