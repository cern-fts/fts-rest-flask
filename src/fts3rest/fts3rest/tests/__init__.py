import os
import shutil
import time

from datetime import datetime, timedelta
from unittest import TestCase
from M2Crypto import ASN1, X509, RSA, EVP
from M2Crypto.ASN1 import UTC


from fts3rest.lib.middleware.fts3auth.credentials import UserCredentials
from fts3rest.model.meta import Session
from fts3.model import Credential, CredentialCache, DataManagement
from fts3.model import Job, File, FileRetryLog, ServerConfig
from fts3rest.config.middleware import create_app
from .ftstestclient import FTSTestClient, TestResponse


def _generate_mock_cert():
    rsa_key = RSA.gen_key(512, 65537)
    pkey = EVP.PKey()
    pkey.assign_rsa(rsa_key)

    cert = X509.X509()
    cert.set_pubkey(pkey)
    not_before = ASN1.ASN1_UTCTIME()
    not_before.set_datetime(datetime.now(UTC))
    not_after = ASN1.ASN1_UTCTIME()
    not_after.set_datetime(datetime.now(UTC) + timedelta(hours=24))
    cert.set_not_before(not_before)
    cert.set_not_after(not_after)
    cert.sign(pkey, "md5")

    return pkey, cert


class TestController(TestCase):
    """
    Base class for the tests
    """

    TEST_USER_DN = "/DC=ch/DC=cern/CN=Test User"

    def setUp(self):
        self.pkey, self.cert = _generate_mock_cert()
        self.flask_app = create_app(test=True)
        self.flask_app.testing = True
        self.flask_app.test_client_class = FTSTestClient
        self.flask_app.response_class = TestResponse
        self.app = self.flask_app.test_client()

    def setup_gridsite_environment(self, no_vo=False, dn=None):
        """
        Add to the test environment mock values of the variables
        set by mod_gridsite.

        Args:
            noVo: If True, no VO attributes will be set
            dn: Override default user DN
        """
        if dn is None:
            dn = TestController.TEST_USER_DN
        self.app.environ_base["GRST_CRED_AURI_0"] = "dn:" + dn

        if not no_vo:
            self.app.environ_base.update(
                {
                    "GRST_CRED_AURI_1": "fqan:/testvo/Role=NULL/Capability=NULL",
                    "GRST_CRED_AURI_2": "fqan:/testvo/Role=myrole/Capability=NULL",
                    "GRST_CRED_AURI_3": "fqan:/testvo/Role=lcgadmin/Capability=NULL",
                }
            )
        else:
            for grst in ["GRST_CRED_AURI_1", "GRST_CRED_AURI_2", "GRST_CRED_AURI_3"]:
                if grst in self.app.environ_base:
                    del self.app.environ_base[grst]

    def get_user_credentials(self):
        """
        Get the user credentials from the environment
        """
        return UserCredentials(self.app.environ_base, {"public": {"*": "all"}})

    def push_delegation(self, lifetime=timedelta(hours=7)):
        """
        Push into the database a mock delegated credential

        Args:
            lifetime: The mock credential lifetime
        """
        creds = self.get_user_credentials()
        delegated = Credential()
        delegated.dlg_id = creds.delegation_id
        delegated.dn = creds.user_dn
        delegated.proxy = "-NOT USED-"
        delegated.voms_attrs = None
        delegated.termination_time = datetime.utcnow() + lifetime

        Session.merge(delegated)
        Session.commit()

    def pop_delegation(self):
        """
        Remove the mock proxy from the database
        """
        cred = self.get_user_credentials()
        if cred and cred.delegation_id:
            delegated = Session.query(Credential).get(
                (cred.delegation_id, cred.user_dn)
            )
            if delegated:
                Session.delete(delegated)
                Session.commit()

    def get_x509_proxy(self, request_pem, issuer=None, subject=None, private_key=None):
        """
        Generate a X509 proxy based on the request

        Args:
            requestPEM: The request PEM encoded
            issuer:     The issuer user
            subject:    The subject of the proxy. If None, issuer/CN=proxy will be  used

        Returns:
            A X509 proxy PEM encoded
        """
        if issuer is None:
            issuer = [("DC", "ch"), ("DC", "cern"), ("CN", "Test User")]
        if subject is None:
            subject = issuer + [("CN", "proxy")]

        x509_request = X509.load_request_string(str(request_pem))

        not_before = ASN1.ASN1_UTCTIME()
        not_before.set_datetime(datetime.now(UTC))
        not_after = ASN1.ASN1_UTCTIME()
        not_after.set_datetime(datetime.now(UTC) + timedelta(hours=3))

        issuer_subject = X509.X509_Name()
        for c in issuer:
            issuer_subject.add_entry_by_txt(c[0], 0x1000, c[1], -1, -1, 0)

        proxy_subject = X509.X509_Name()
        for c in subject:
            proxy_subject.add_entry_by_txt(c[0], 0x1000, c[1], -1, -1, 0)

        proxy = X509.X509()
        proxy.set_version(2)
        proxy.set_subject(proxy_subject)
        proxy.set_serial_number(int(time.time()))
        proxy.set_version(x509_request.get_version())
        proxy.set_issuer(issuer_subject)
        proxy.set_pubkey(x509_request.get_pubkey())

        proxy.set_not_after(not_after)
        proxy.set_not_before(not_before)

        if not private_key:
            proxy.sign(self.pkey, "sha1")
        else:
            proxy.sign(private_key, "sha1")

        return proxy.as_pem() + self.cert.as_pem()

    def get_real_x509_proxy(self):
        """
        Get a real X509 proxy

        Returns:
            The content of the file pointed by X509_USER_PROXY,
            None otherwise
        """
        proxy_path = os.environ.get("X509_USER_PROXY", None)
        if not proxy_path:
            return None
        return open(proxy_path).read()

    def tearDown(self):
        """
        Called by the test framework at the end of each test
        """
        Session.query(Credential).delete()
        Session.query(CredentialCache).delete()
        Session.query(FileRetryLog).delete()
        Session.query(File).delete()
        Session.query(DataManagement).delete()
        Session.query(Job).delete()
        Session.query(ServerConfig).delete()
        Session.commit()

        # Delete messages
        if "fts3.MessagingDirectory" in self.flask_app.config:
            try:
                shutil.rmtree(self.flask_app.config["fts3.MessagingDirectory"])
            except Exception:
                pass

        self.flask_app.do_teardown_appcontext()
