import logging
from datetime import datetime

import jwt
from oic import rndstr
from oic.extension.message import TokenIntrospectionRequest, TokenIntrospectionResponse
from oic.oic import Client, Grant, Token
from oic.oic.message import AccessTokenResponse, Message, RegistrationResponse
from oic.utils import time_util
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

log = logging.getLogger(__name__)


class OIDCmanager:
    """
    Class that interfaces with PyOIDC

    It is supposed to have a unique instance which provides all operations that require
    information from the OIDC issuers.
    """

    def __init__(self):
        self.clients = {}
        self.clients_config = {}
        self.config = None

    def setup(self, config):
        self.config = config
        self._configure_clients(config["fts3.Providers"])
        self._set_keys_cache_time(config["fts3.JWKCacheSeconds"])
        self._retrieve_clients_keys()

    def _configure_clients(self, providers_config):
        for provider in providers_config:
            try:
                client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
                # Retrieve well-known configuration
                client.provider_config(provider)
                # Register
                client_reg = RegistrationResponse(
                    client_id=providers_config[provider]["client_id"],
                    client_secret=providers_config[provider]["client_secret"],
                )
                client.store_registration_info(client_reg)
                issuer = client.provider_info["issuer"]
                if "introspection_endpoint" not in client.provider_info:
                    log.warning("{} -- missing introspection endpoint".format(issuer))
                self.clients[issuer] = client
                # Store custom configuration options for this provider
                self.clients_config[issuer] = providers_config[provider]["custom"]
            except Exception as ex:
                log.warning("Exception registering provider: {}".format(provider))
                log.warning(ex)

    def _retrieve_clients_keys(self):
        for issuer, client in self.clients.items():
            client.keyjar.get_issuer_keys(issuer)

    def _set_keys_cache_time(self, cache_time):
        for issuer, client in self.clients.items():
            keybundles = client.keyjar.issuer_keys[issuer]
            for keybundle in keybundles:
                keybundle.cache_time = cache_time

    def retrieve_client(self, issuer):
        if issuer in self.clients:
            return self.clients.get(issuer), issuer
        elif issuer + "/" in self.clients:
            return self.clients.get(issuer + "/"), issuer + "/"
        else:
            raise ValueError("Could not retrieve client for issuer={}".format(issuer))

    def token_issuer_supported(self, access_token):
        """
        Given an access token, checks whether a client is registered
        for the token issuer.
        :param access_token:
        :return: true if token issuer is supported, false otherwise
        :raise KeyError: issuer claim missing
        """
        unverified_payload = jwt.decode(access_token, options=jwt_options_unverified())
        issuer = unverified_payload["iss"]
        log.debug("Checking client registration for issuer={}".format(issuer))
        try:
            return self.retrieve_client(issuer) is not None
        except ValueError:
            log.warning(
                "Could not find client registration for issuer={}".format(issuer)
            )
            return False

    def filter_provider_keys(self, issuer, kid=None, alg=None):
        """
        Return Provider Keys after applying Key ID and Algorithm filter.
        If no filters match, return the full set.
        :param issuer: provider
        :param kid: Key ID
        :param alg: Algorithm
        :return: keys
        :raise ValueError: client could not be retrieved
        """
        client, issuer = self.retrieve_client(issuer)
        # List of Keys (from pyjwkest)
        keys = client.keyjar.get_issuer_keys(issuer)
        filtered_keys = [key for key in keys if key.kid == kid or key.alg == alg]
        if len(filtered_keys) is 0:
            return keys
        return filtered_keys

    def introspect(self, issuer, access_token):
        """
        Make a Token Introspection request
        :param issuer: issuer of the token
        :param access_token: token to introspect
        :return: JSON response
        """
        client, _ = self.retrieve_client(issuer)
        if "introspection_endpoint" not in client.provider_info:
            raise Exception("Issuer does not support introspection")
        response = client.do_any(
            request_args={"token": access_token},
            request=TokenIntrospectionRequest,
            response=TokenIntrospectionResponse,
            body_type="json",
            method="POST",
            authn_method="client_secret_basic",
        )
        return response

    def generate_refresh_token(self, issuer, token, audience=None, scope=None):
        """
        Exchange an access token for a refresh token.
        If the scopes are specified, ensure "offline_access" is part of the claim.
        If the audience is not specified, use the client ID.
        :param issuer: issuer of the access token
        :param audience: audience of the access token
        :param scope: scope string of the access token
        :param token: the access token
        :return: refresh token
        :raise Exception: If refresh token cannot be obtained
        """
        client, issuer = self.retrieve_client(issuer)
        body = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requested_token_type": "urn:ietf:params:oauth:token-type:refresh_token",
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "subject_token": token,
        }

        # Handle custom audience from config
        if "audience" in self.clients_config[issuer]:
            config_audience = self.clients_config[issuer]["audience"]
            log.debug(
                'Using client_config_options["{}"]["audience"]={}'.format(
                    issuer, config_audience
                )
            )
            if audience is None:
                audience = config_audience
            else:
                if isinstance(audience, str):
                    audience = [audience]
                audience.append(config_audience)

        # Handle "requested_token_type" grant
        if "no_requested_token_type" in self.clients_config[issuer]:
            del body["requested_token_type"]

        if scope:
            body["scope"] = " ".join(scope)
            if "offline_access" not in scope:
                body["scope"] += " offline_access"
        if audience:
            body["audience"] = audience

        log.debug(
            "generate_refresh_token: issuer={} audience={} scope={}".format(
                issuer, audience, scope
            )
        )

        try:
            response = client.do_any(
                Message,
                request_args=body,
                endpoint=client.provider_info["token_endpoint"],
                body_type="json",
                method="POST",
                authn_method="client_secret_basic",
            )
            response = response.json()
            log.debug("generate_refresh_token response::: {}".format(response))
            access_token = response.get("access_token", token)
            refresh_token = response.get("refresh_token")
            if access_token == refresh_token:
                access_token = token
        except Exception as ex:
            log.warning("Exception during refresh token request: {}".format(ex))
            raise Exception("Exception during refresh token request: {}".format(ex))
        if refresh_token is None:
            errmsg = "No refresh token returned during token exchange"
            if scope is None:
                errmsg += '. Is "offline_access" scope included?'
            elif "offline_access" not in scope:
                errmsg += ". Token must contain offline_access scope!"
            raise Exception(errmsg)
        return access_token, refresh_token

    def refresh_access_token(self, credential):
        """
        Request new access token
        :param credential: Credential from DB containing an access token and a refresh token
        :return: Updated credential containing new access token
        """
        access_token, refresh_token = credential.proxy.split(":")
        unverified_payload = jwt.decode(access_token, options=jwt_options_unverified())
        issuer = unverified_payload["iss"]
        log.debug(
            "refresh_access_token::: issuer={} subject={}".format(issuer, credential.dn)
        )
        client, _ = self.retrieve_client(issuer)

        # Prepare and make request
        refresh_session_state = rndstr(50)
        client.grant[refresh_session_state] = Grant()
        client.grant[refresh_session_state].grant_expiration_time = (
            time_util.utc_time_sans_frac() + 60
        )
        resp = AccessTokenResponse()
        resp["refresh_token"] = refresh_token
        client.grant[refresh_session_state].tokens.append(Token(resp))
        new_credential = client.do_access_token_refresh(
            authn_method="client_secret_basic", state=refresh_session_state
        )
        # A new refresh token is optional
        refresh_token = new_credential.get("refresh_token", refresh_token)
        access_token = new_credential.get("access_token")
        unverified_payload = jwt.decode(access_token, options=jwt_options_unverified())
        expiration_time = unverified_payload["exp"]
        credential.proxy = new_credential["access_token"] + ":" + refresh_token
        credential.termination_time = datetime.utcfromtimestamp(expiration_time)

        return credential

    @staticmethod
    def jwt_options_unverified(options=None):
        options_unverified = {
            "verify_signature": False,
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iat": False,
            "verify_aud": False,
            "verify_iss": False,
        }
        if options is not None:
            options_unverified.update(options)
        return options_unverified


# Should be the only instance, called during the middleware initialization
oidc_manager = OIDCmanager()
jwt_options_unverified = OIDCmanager.jwt_options_unverified
