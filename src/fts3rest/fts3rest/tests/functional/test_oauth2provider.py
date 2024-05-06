from fts3rest.lib.oauth2provider import FTS3OAuth2ResourceProvider
from fts3rest.lib.openidconnect import OIDCmanager
from fts3rest.tests import TestController
import unittest


class TestFTS3OAuth2ResourceProvider(TestController):
    """
    Test token validation

    To run these tests, the host should have oidc-agent installed,
    with an account 'xdctest'
    """

    def setUp(self):
        super().setUp()
        config = self.flask_app.config
        if not config["fts3.Providers"]:
            raise unittest.SkipTest("Missing OIDC client configuration data")
        config["fts3.OAuth2"] = True
        self.oidc_manager = OIDCmanager()
        self.issuer = "https://iam.extreme-datacloud.eu/"
        self.oidc_manager.setup(config)
        self.oauth2_resource_provider = FTS3OAuth2ResourceProvider(dict(), config)
        self.expired_token = "eyJraWQiOiJyc2ExIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiI5NGQyNTQyOS1mYTZhLTRiYTctOGM0NS1mMTk1YjI3ZWVkNjMiLCJpc3MiOiJodHRwczpcL1wvaWFtLmV4dHJlbWUtZGF0YWNsb3VkLmV1XC8iLCJleHAiOjE1ODAyMjIyMDksImlhdCI6MTU4MDIxODYwOSwianRpIjoiYTI0NDRhYTQtNTE3YS00Y2E0LTgwMTUtY2IyMjc0Nzg4YzlkIn0.hvTjA-Ix_YVxU3HmLB6FQa98eYtUwbw1WcZMO5p_qOjnPwD0OtQViVtV-a5__hLY1_qRFouAzgVvqKnueokh1pmKoI6TJN2KpmybueAZR30lIG_t_aAn4hGQvuVezs_0LLISojQUgprbi2PDsU1q8WTJq1J5mwGwlBijGmHQs60"

    def test_validate_access_token(self):
        token = self._get_xdc_access_token()
        auth = self.oauth2_resource_provider.authorization_class()
        self.oauth2_resource_provider.validate_access_token(token, auth)
        self.assertTrue(auth.is_valid)

    def test_validate_token_offline(self):
        token = self._get_xdc_access_token()
        valid, credential = self.oauth2_resource_provider._validate_token_offline(token)
        self.assertTrue(valid)
        self.assertEqual(credential["iss"], self.issuer)

    def test_validate_token_online(self):
        token = self._get_xdc_access_token()
        valid, credential = self.oauth2_resource_provider._validate_token_online(token)
        self.assertTrue(valid)
        self.assertEqual(credential["iss"], self.issuer)

    def test_validate_access_token_invalid(self):
        token = self._get_xdc_access_token()
        token += "invalid"
        auth = self.oauth2_resource_provider.authorization_class()
        self.oauth2_resource_provider.validate_access_token(token, auth)
        self.assertFalse(auth.is_valid)

    def test_validate_token_offline_invalid(self):
        token = self._get_xdc_access_token()
        token += "invalid"
        valid, credential = self.oauth2_resource_provider._validate_token_offline(token)
        self.assertFalse(valid)

    def test_validate_token_online_invalid(self):
        token = self._get_xdc_access_token()
        token += "invalid"
        valid, credential = self.oauth2_resource_provider._validate_token_online(token)
        self.assertFalse(valid)

    def test_validate_access_token_expired(self):
        token = self.expired_token
        auth = self.oauth2_resource_provider.authorization_class()
        self.oauth2_resource_provider.validate_access_token(token, auth)
        self.assertFalse(auth.is_valid)
        self.assertTrue(auth.error)

    def test_validate_token_offline_expired(self):
        token = self.expired_token
        with self.assertRaises(Exception):
            self.oauth2_resource_provider._validate_token_offline(token)

    def test_validate_token_online_expired(self):
        token = self.expired_token
        valid, credential = self.oauth2_resource_provider._validate_token_online(token)
        self.assertFalse(valid)
