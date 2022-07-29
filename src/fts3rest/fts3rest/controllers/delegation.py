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

import json
import logging
import os
import re
import shlex
import M2Crypto.threading

from datetime import datetime
from M2Crypto import X509, RSA, EVP, BIO
import flask
from flask import Response
from flask import current_app as app
from flask.views import View
from fts3rest.model import CredentialCache, Credential
from fts3rest.model.meta import Session
from fts3rest.lib.helpers.voms import VomsClient, VomsException
from fts3rest.lib.middleware.fts3auth.authorization import require_certificate
from fts3rest.lib.JobBuilder_utils import get_base_id, get_vo_id
from fts3rest.templates.mako import render_template
from werkzeug.exceptions import NotFound, BadRequest, Forbidden, FailedDependency
from fts3rest.lib.helpers.jsonify import jsonify

log = logging.getLogger(__name__)


class ProxyException(Exception):
    pass


def _mute_callback(*args, **kwargs):
    """
    Does nothing. Used as a callback for gen_key
    """
    pass


def _populated_x509_name(components):
    """
    Generates a populated X509_Name with the entries passed in components
    """
    x509_name = X509.X509_Name()
    for field, value in components:
        x509_name.add_entry_by_txt(field, 0x1000, value, len=-1, loc=-1, set=0)
    return x509_name


def _generate_proxy_request(key_len=2048):
    """
    Generates a X509 proxy request.

    Args:
        key_len: Length of the RSA key in bits

    Returns:
        A tuple (X509 request, generated private key)
    """
    key_pair = RSA.gen_key(key_len, 65537, callback=_mute_callback)
    pkey = EVP.PKey()
    pkey.assign_rsa(key_pair)
    x509_request = X509.Request()
    x509_request.set_pubkey(pkey)
    x509_request.set_subject(_populated_x509_name([("O", "Dummy")]))
    x509_request.set_version(0)
    x509_request.sign(pkey, "sha256")

    return x509_request, pkey


def _read_x509_list(x509_pem):
    """
    Loads the list of certificates contained in x509_pem
    """
    x509_list = []
    bio = BIO.MemoryBuffer(x509_pem)
    try:
        while bio.readable():
            cert = X509.load_cert_bio(bio)
            x509_list.append(cert)
    except X509.X509Error:
        pass
    return x509_list


def _validate_proxy(proxy_pem, private_key_pem):
    """
    Validates a proxy being put by the client

    Args:
        proxy_pem: The PEM representation of the proxy
        private_key_pem: The PEM representation of the private key

    Returns:
        The proxy expiration time

    Raises:
        ProxyException: If the validation fails
    """
    x509_list = _read_x509_list(proxy_pem)
    if len(x509_list) < 2:
        raise ProxyException("Malformed proxy")
    x509_proxy = x509_list[0]
    x509_proxy_issuer = x509_list[1]

    expiration_time = min(map(lambda f: f.get_not_after().get_datetime().replace(tzinfo=None), x509_list))
    private_key = EVP.load_key_string(private_key_pem, callback=_mute_callback)

    # The modulus of the stored private key and the modulus of the proxy must match
    if x509_proxy.get_pubkey().get_modulus() != private_key.get_modulus():
        raise ProxyException(
            "The proxy does not match the stored associated private key"
        )

    # Verify the issuer
    if x509_proxy.verify(x509_proxy_issuer.get_pubkey()) < 1:
        raise ProxyException(
            "Failed to verify the proxy, maybe signed with the wrong private key?"
        )

    # Validate the subject
    subject = x509_proxy.get_subject().as_text().split(", ")
    issuer = x509_proxy.get_issuer().as_text().split(", ")
    if subject[:-1] != issuer:
        raise ProxyException(
            "The subject and the issuer of the proxy do not match: %s != %s"
            % (x509_proxy.get_subject().as_text(), x509_proxy.get_issuer().as_text())
        )
    elif not subject[-1].startswith("CN="):
        raise ProxyException("Missing trailing Common Name in the proxy")
    else:
        log.debug("Delegated DN: " + "/".join(subject))

    return expiration_time


def _build_full_proxy(x509_pem, privkey_pem):
    """
    Generates a full proxy from the input parameters.
    A valid full proxy has this format: proxy, private key, certificate chain
    Args:
        proxy_pem: The certificate chain
        privkey_pem: The private key
    Returns:
        A full proxy
    """
    x509_list = _read_x509_list(x509_pem)
    x509_chain = b"".join(map(lambda x: x.as_pem(), x509_list[1:]))
    return x509_list[0].as_pem() + privkey_pem + x509_chain


def _build_certificate():
    """
    Generates a user certificate from the environment

    Returns:
        Returns the user certificate
    """
    n = 0
    full_cert = ""
    cert = flask.request.environ.get("SSL_CLIENT_CERT", None)
    while cert:
        full_cert += cert
        cert = flask.request.environ.get("SSL_CLIENT_CERT_CHAIN_%d" % n, None)
        n += 1
    if len(full_cert) > 0:
        ret = full_cert
    else:
        ret = None
    return ret


def _adapt_response(user_agent):
    match = re.compile("""fts-.+/(\d+)\.(\d+)""").search(user_agent)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        if major > 3:
            return False
        elif major == 3 and minor >= 12:
            return False
    return True


class Delegation(View):
    """
    Operations to perform the delegation of credentials
    """

    def __init__(self):
        """
        Constructor
        """
        M2Crypto.threading.init()

        vomses_dir = "/etc/vomses"
        vo_set = set()
        try:
            vomses = os.listdir(vomses_dir)
            for voms in vomses:
                voms_cfg = os.path.join(vomses_dir, voms)
                lines = filter(
                    lambda l: len(l) and l[0] != "#",
                    map(str.strip, open(voms_cfg).readlines()),
                )
                for l in lines:
                    vo_set.add(shlex.split(l)[0])
            self.vo_list = list(sorted(vo_set))
        except Exception:
            pass


class whoami(Delegation):
    @jsonify
    def dispatch_request(self):
        """
        Returns the active credentials of the user
        """
        whoami = flask.request.environ["fts3.User.Credentials"]
        whoami.base_id = str(get_base_id())
        for vo in whoami.vos:
            whoami.vos_id.append(str(get_vo_id(vo)))
        return whoami


class certificate(Delegation):
    @require_certificate
    def dispatch_request(self):
        """
        Returns the user certificate
        """
        ret = _build_certificate()
        return Response(ret, mimetype="application/x-pem-file")


class view(Delegation):
    @jsonify
    def dispatch_request(self, dlg_id):
        """
        Get the termination time of the current delegated credential, if any
        """
        user = flask.request.environ["fts3.User.Credentials"]

        user_agent = flask.request.environ.get("HTTP_USER_AGENT", None)

        if dlg_id != user.delegation_id:
            raise Forbidden("The requested ID and the credentials ID do not match")

        cred = Session.query(Credential).get((user.delegation_id, user.user_dn))
        if not cred:
            if user_agent is None or _adapt_response(user_agent):
                return None  # FTS-1734: Assure backwards compatibility with old clients who expect a null response
            else:
                ret = None
        else:
            log.info(
                "dlg_id=%s termination_time=%s"
                % (user.delegation_id, cred.termination_time)
            )
            ret = {
                "termination_time": cred.termination_time,
                "voms_attrs": cred.voms_attrs.split("\n"),
            }
        return Response(ret, mimetype="application/json")


class delete(Delegation):
    @require_certificate
    def dispatch_request(self, dlg_id):
        """
        Delete the delegated credentials from the database
        """
        user = flask.request.environ["fts3.User.Credentials"]

        if dlg_id != user.delegation_id:
            raise Forbidden("The requested ID and the credentials ID do not match")

        cred = Session.query(Credential).get((user.delegation_id, user.user_dn))
        if not cred:
            raise NotFound("Delegated credentials not found")
        else:
            try:
                Session.delete(cred)
                Session.commit()
            except Exception:
                Session.rollback()
                raise
            return Response([""], status=204)


class request(Delegation):
    @require_certificate
    def dispatch_request(self, dlg_id):
        """
        First step of the delegation process: get a certificate request

        The returned certificate request must be signed with the user's original
        credentials.
        """
        user = flask.request.environ["fts3.User.Credentials"]

        if dlg_id != user.delegation_id:
            raise Forbidden("The requested ID and the credentials ID do not match")

        credential_cache = Session.query(CredentialCache).get(
            (user.delegation_id, user.user_dn)
        )

        user_cert = _build_certificate()

        request_key_len = 2048
        if user_cert:
            user_key = X509.load_cert_string(user_cert)
            request_key_len = user_key.get_pubkey().size() * 8

        cached = (
            credential_cache is not None and credential_cache.cert_request is not None
        )
        if cached:
            cached_key_len = (
                X509.load_request_string(credential_cache.cert_request)
                .get_pubkey()
                .size()
                * 8
            )
            if cached_key_len != request_key_len:
                cached = False
                log.debug(
                    "Invalidating cache due to key length missmatch between client and cached certificates"
                )

        if not cached:
            (x509_request, private_key) = _generate_proxy_request(request_key_len)
            credential_cache = CredentialCache(
                dlg_id=user.delegation_id,
                dn=user.user_dn,
                cert_request=x509_request.as_pem(),
                priv_key=private_key.as_pem(cipher=None),
                voms_attrs=" ".join(user.voms_cred),
            )
            try:
                Session.merge(credential_cache)
                Session.commit()
            except Exception:
                Session.rollback()
                raise
            log.debug("Generated new credential request for %s" % dlg_id)
        else:
            log.debug("Using cached request for %s" % dlg_id)
        resp = Response([credential_cache.cert_request], mimetype="text/plain")
        resp.headers["X-Delegation-ID"] = str(credential_cache.dlg_id)
        return resp


class credential(Delegation):
    @require_certificate
    def dispatch_request(self, dlg_id):
        """
        Second step of the delegation process: put the generated certificate

        The certificate being PUT will have to pass the following validation:
            - There is a previous certificate request done
            - The certificate subject matches the certificate issuer + '/CN=Proxy'
            - The certificate modulus matches the stored private key modulus
        """
        user = flask.request.environ["fts3.User.Credentials"]

        if dlg_id != user.delegation_id:
            raise Forbidden("The requested ID and the credentials ID do not match")

        credential_cache = Session.query(CredentialCache).get(
            (user.delegation_id, user.user_dn)
        )
        if credential_cache is None:
            raise BadRequest("No credential cache found")

        x509_proxy_pem = flask.request.data
        log.debug("Received delegated credentials for %s" % dlg_id)
        log.debug(x509_proxy_pem)

        if credential_cache.priv_key and isinstance(credential_cache.priv_key, str):
            priv_key = bytes(credential_cache.priv_key, "utf-8")
        else:
            priv_key = credential_cache.priv_key
        try:
            expiration_time = _validate_proxy(x509_proxy_pem, priv_key)
            x509_full_proxy_pem = _build_full_proxy(x509_proxy_pem, priv_key)
        except ProxyException as ex:
            raise BadRequest("Could not process the proxy: " + str(ex))

        credential = Credential(
            dlg_id=user.delegation_id,
            dn=user.user_dn,
            proxy=x509_full_proxy_pem,
            voms_attrs=credential_cache.voms_attrs,
            termination_time=expiration_time,
        )

        try:
            Session.merge(credential)
            Session.commit()
        except Exception:
            Session.rollback()
            raise
        return Response([""], status=201)


class voms(Delegation):
    @require_certificate
    def dispatch_request(self, dlg_id):
        """
        Generate VOMS extensions for the delegated proxy

        The input must be a json-serialized list of strings, where each strings
        is a voms command (i.e. ["dteam", "dteam:/dteam/Role=lcgadmin"])
        """
        user = flask.request.environ["fts3.User.Credentials"]

        if dlg_id != user.delegation_id:
            raise Forbidden("The requested ID and the credentials ID do not match")

        try:
            voms_list = json.loads(flask.request.data)
            log.debug(
                "VOMS request received for %s: %s" % (dlg_id, ", ".join(voms_list))
            )
            if not isinstance(voms_list, list):
                raise Exception("Expecting a list of strings")
        except Exception as ex:
            raise BadRequest(str(ex))

        credential = Session.query(Credential).get((user.delegation_id, user.user_dn))

        if credential.termination_time <= datetime.utcnow():
            raise Forbidden("Delegated proxy already expired")

        try:
            voms_client = VomsClient(credential.proxy)
            (new_proxy, new_termination_time) = voms_client.init(voms_list)
        except VomsException as ex:
            # Error generating the proxy because of the request itself
            raise FailedDependency(str(ex))

        credential.proxy = new_proxy
        credential.termination_time = new_termination_time
        credential.voms_attrs = " ".join(voms_list)

        try:
            Session.merge(credential)
            Session.commit()
        except Exception:
            Session.rollback()
            raise

        return Response([str(new_termination_time)], status=203, mimetype="text/plain")


class delegation_page(Delegation):
    @require_certificate
    def dispatch_request(self):
        """
        Render an HTML form to delegate the credentials
        """
        user = flask.request.environ["fts3.User.Credentials"]
        return render_template(
            "/delegation.html",
            **{
                "user": user,
                "vos": self.vo_list,
                "certificate": flask.request.environ.get("SSL_CLIENT_CERT", None),
                "site": app.config["fts3.SiteName"],
            },
        )
