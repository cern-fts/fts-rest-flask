from fts3rest.model import Credential
from fts3rest.lib.openidconnect import OIDCmanager
from fts3rest.tests import TestController
import unittest


class TestOpenidconnect(TestController):
    """
    Tests OIDCmanager operations

    To run these tests, the host should have oidc-agent installed,
    with an account 'xdctest'
    """

    def setUp(self):
        super().setUp()
        self.oidc_manager = OIDCmanager()
        self.config = self.flask_app.config
        self.issuer = "https://iam.extreme-datacloud.eu/"
        if "client_id" not in self.config["fts3.Providers"][self.issuer]:
            raise unittest.SkipTest("Missing OIDC client configurationd data")

    def test_configure_clients(self):
        self.oidc_manager._configure_clients(self.config["fts3.Providers"])
        self.assertEqual(
            len(self.oidc_manager.clients), len(self.config["fts3.Providers"])
        )

    def test_introspect(self):
        self.oidc_manager.setup(self.config)
        access_token = self._get_xdc_access_token()
        response = self.oidc_manager.introspect(self.issuer, access_token)
        self.assertTrue(response["active"])

    def test_generate_refresh_token(self):
        self.oidc_manager.setup(self.config)
        access_token = self._get_xdc_access_token()
        self.oidc_manager.generate_refresh_token(self.issuer, access_token)

    def test_generate_refresh_token_invalid(self):
        self.oidc_manager.setup(self.config)
        access_token = self._get_xdc_access_token()
        access_token += "invalid"
        with self.assertRaises(Exception):
            self.oidc_manager.generate_refresh_token(self.issuer, access_token)

    def test_refresh_access_token(self):
        self.oidc_manager.setup(self.config)
        access_token = self._get_xdc_access_token()
        refresh_token = self.oidc_manager.generate_refresh_token(
            self.issuer, access_token
        )
        credential = Credential()
        credential.proxy = ":".join([access_token, refresh_token])
        new_credential = self.oidc_manager.refresh_access_token(credential)
        self.assertIsNotNone(new_credential.termination_time)
