from types import SimpleNamespace
from unittest import mock

from fts3rest.lib.middleware.fts3auth.authorization import authorized
from fts3rest.lib.middleware.fts3auth.constants import TRANSFER, CONFIG, ADMIN
from fts3rest.lib.middleware.fts3auth.constants import NONE, PRIVATE, VO, ALL
from fts3rest.lib.middleware.fts3auth.credentials import UserCredentials
from fts3rest.model.meta import Session
from fts3rest.model import AuthorizationByDn
from fts3rest.tests import TestController


ROLES = {
    "public": {"transfer": ""},
    "lcgadmin": {"transfer": "vo"},
    "ftsadmin": {"config": "all"},
}

TOKEN_SUBJECT = "60921763-d4a2-49bb-b790-a17fabdb4f2b"
TOKEN_ISSUER = "https://iam.example/"
TOKEN_VO = "iam.example"


class _MockOAuth2ResourceProvider:
    """
    Mock the "FTSOAuth2ResourceProvider" class
    """

    def __init__(self, environ, config):
        pass

    def get_authorization(self):
        return SimpleNamespace(
            is_oauth=True,
            is_valid=True,
            error=None,
            subject=TOKEN_SUBJECT,
            issuer=TOKEN_ISSUER,
            scope=["fts"],
            wlcg_profile="1.0",
            groups=None,
        )


class TestAuthorization(TestController):
    """
    Test the FTS-REST authorization object
    """

    def setUp(self):
        super().setUp()
        self.setup_gridsite_environment()
        Session.query(AuthorizationByDn).delete()
        Session.commit()

    def tearDown(self):
        Session.query(AuthorizationByDn).delete()
        Session.commit()
        super().tearDown()

    def _database_grant(self, dn, operation):
        Session.merge(AuthorizationByDn(dn=dn, operation=operation))
        Session.commit()

    def _cert_user(self):
        return UserCredentials(env=self.app.environ_base, role_permissions=ROLES)

    def _token_user(self):
        with mock.patch(
            "fts3rest.lib.oauth2provider.FTS3OAuth2ResourceProvider",
            _MockOAuth2ResourceProvider,
        ):
            return UserCredentials(env={}, role_permissions=ROLES, config={})

    @staticmethod
    def _authorized(user, operation, owner=None, vo=None):
        """
        Wrapper on top of the main "authorization" function,
        which returns if the user is authorized to perform the operation
        """

        return authorized(
            operation,
            resource_owner=owner,
            resource_vo=vo,
            env={"fts3.User.Credentials": user},
        )

    def test_anonymous(self):
        """
        Test authorization permissions for anonymous user
        """
        user = UserCredentials({}, {}, {})
        self.assertEqual(user.user_dn, "anon")
        self.assertEqual(user.method, "unauthenticated")
        self.assertIsNone(user.get_granted_level_for(TRANSFER))
        self.assertIsNone(user.get_granted_level_for(CONFIG))
        self.assertIsNone(user.get_granted_level_for(ADMIN))
        self.assertIsNone(self._authorized(user, TRANSFER))

    def test_cert_public(self):
        """
        Test authorization permissions for certificate with "Public" role
        """
        self.setup_gridsite_environment(no_vo=True)
        user = self._cert_user()
        self.assertEqual(user.user_dn, TestController.TEST_USER_DN)
        self.assertEqual(user.method, "certificate")
        self.assertEqual(user.get_granted_level_for(TRANSFER), PRIVATE)
        self.assertEqual(user.get_granted_level_for(CONFIG), NONE)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(self._authorized(user, TRANSFER))
        self.assertTrue(
            self._authorized(user, TRANSFER, owner=user.user_dn, vo="othervo")
        )
        self.assertFalse(
            self._authorized(user, TRANSFER, owner="/CN=other", vo=user.vos[0])
        )
        self.assertFalse(
            self._authorized(user, TRANSFER, owner="/CN=other", vo="othervo")
        )
        self.assertFalse(self._authorized(user, CONFIG))
        self.assertFalse(self._authorized(user, ADMIN))

    def test_cert_role_grant(self):
        """
        Test authorization permissions for certificate with specific role
        """
        user = self._cert_user()
        self.assertEqual(user.get_granted_level_for(TRANSFER), VO)
        self.assertEqual(user.get_granted_level_for(CONFIG), NONE)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(
            self._authorized(user, TRANSFER, owner=user.user_dn, vo="othervo")
        )
        self.assertTrue(
            self._authorized(user, TRANSFER, owner="/CN=other", vo="testvo")
        )
        self.assertFalse(
            self._authorized(user, TRANSFER, owner="/CN=other", vo="othervo")
        )

    def test_cert_role_grant_config(self):
        """
        Test authorization permissions for certificate with role offering config rights
        """
        self.setup_gridsite_environment(ftsadmin=True)
        user = self._cert_user()
        self.assertEqual(user.config_level, CONFIG)
        self.assertEqual(user.get_granted_level_for(TRANSFER), VO)
        self.assertEqual(user.get_granted_level_for(CONFIG), ALL)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(self._authorized(user, CONFIG))
        self.assertFalse(self._authorized(user, ADMIN))

    def test_cert_database_grant_config(self):
        """
        Test authorization permissions for certificate with database config grant
        """
        self._database_grant(TestController.TEST_USER_DN, CONFIG)
        user = self._cert_user()
        self.assertEqual(user.config_level, CONFIG)
        self.assertEqual(user.get_granted_level_for(TRANSFER), VO)
        self.assertEqual(user.get_granted_level_for(CONFIG), ALL)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(self._authorized(user, CONFIG))
        self.assertFalse(self._authorized(user, ADMIN))

    def test_cert_database_grant_admin(self):
        """
        Test authorization permissions for certificate with database admin grant
        """
        self._database_grant(TestController.TEST_USER_DN, ADMIN)
        user = self._cert_user()
        self.assertEqual(user.config_level, ADMIN)
        self.assertEqual(user.get_granted_level_for(TRANSFER), VO)
        self.assertEqual(user.get_granted_level_for(CONFIG), ALL)
        self.assertEqual(user.get_granted_level_for(ADMIN), ALL)
        self.assertTrue(self._authorized(user, CONFIG))
        self.assertTrue(self._authorized(user, ADMIN))

    def test_token_public(self):
        """
        Test authorization permissions for token with "Public" role
        """
        user = self._token_user()
        self.assertEqual(user.user_dn, TOKEN_SUBJECT)
        self.assertEqual(user.method, "oauth2")
        self.assertEqual(getattr(user, "oauth2_scope"), "fts")
        self.assertEqual(user.get_granted_level_for(TRANSFER), PRIVATE)
        self.assertEqual(user.get_granted_level_for(CONFIG), NONE)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(self._authorized(user, TRANSFER))
        self.assertTrue(
            self._authorized(user, TRANSFER, owner=TOKEN_SUBJECT, vo="othervo")
        )
        self.assertFalse(
            self._authorized(user, TRANSFER, owner="other-token-subject", vo=TOKEN_VO)
        )
        self.assertFalse(
            self._authorized(user, TRANSFER, owner="other-token-subject", vo="othervo")
        )
        self.assertFalse(self._authorized(user, CONFIG))
        self.assertFalse(self._authorized(user, ADMIN))

    def test_token_database_grant_config(self):
        """
        Test authorization permissions for token with database config grant
        """
        self._database_grant(TOKEN_SUBJECT, CONFIG)
        user = self._token_user()
        self.assertEqual(user.config_level, CONFIG)
        self.assertEqual(user.get_granted_level_for(TRANSFER), PRIVATE)
        self.assertEqual(user.get_granted_level_for(CONFIG), ALL)
        self.assertEqual(user.get_granted_level_for(ADMIN), NONE)
        self.assertTrue(self._authorized(user, CONFIG))
        self.assertFalse(self._authorized(user, ADMIN))

    def test_token_database_grant_admin(self):
        """
        Test authorization permissions for token with database admin grant
        """
        self._database_grant(TOKEN_SUBJECT, ADMIN)
        user = self._token_user()
        self.assertEqual(user.config_level, ADMIN)
        self.assertEqual(user.get_granted_level_for(TRANSFER), PRIVATE)
        self.assertEqual(user.get_granted_level_for(CONFIG), ALL)
        self.assertEqual(user.get_granted_level_for(ADMIN), ALL)
        self.assertTrue(self._authorized(user, CONFIG))
        self.assertTrue(self._authorized(user, ADMIN))
