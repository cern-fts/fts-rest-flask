import unittest
from fts3rest.lib.middleware.fts3auth.credentials import UserCredentials
from fts3rest.lib.middleware.fts3auth.authorization import authorized, authorize
from fts3rest.lib.middleware.fts3auth.constants import *
from fts3rest.model.meta import Session
from fts3.model import AuthorizationByDn
from werkzeug.exceptions import Forbidden


class TestAuthorization(unittest.TestCase):
    """
    Tests for the authorization code.
    The environment is initialized with the DN and FQANS bellow,
    and uses the configuration specified by ROLES.
    """

    DN = "/DC=ch/DC=cern/CN=Test User"
    FQANS = [
        "/testvo/Role=NULL/Capability=NULL",
        "/testvo/group/Role=NULL/Capability=NULL",
        "/testvo/Role=myrole/Capability=NULL",
    ]

    # Any user can handle his/her own transfers, and vo transfers
    # Any user can delegate
    # No user can run configuration actions
    ROLES = {"public": {"transfer": "vo", "deleg": "all"}}

    def setUp(self):
        env = dict()
        env["GRST_CRED_AURI_0"] = "dn:" + TestAuthorization.DN
        env["GRST_CRED_AURI_1"] = "fqan:" + TestAuthorization.FQANS[0]
        env["GRST_CRED_AURI_2"] = "fqan:" + TestAuthorization.FQANS[1]
        env["GRST_CRED_AURI_3"] = "fqan:" + TestAuthorization.FQANS[2]

        self.creds = UserCredentials(env, TestAuthorization.ROLES)

        env["fts3.User.Credentials"] = self.creds
        self.env = env

    def tearDown(self):
        Session.query(AuthorizationByDn).delete()

    def test_authorized_base(self):
        """
        Try to perform an action that is not configured (must be denied), and another
        one that is allowed for everyone
        """
        self.assertFalse(authorized(CONFIG, env=self.env))
        self.assertTrue(authorized(DELEGATION, env=self.env))

    def test_authorized_vo(self):
        """
        Try to perform an action that is allowed only for users belonging to the same
        vo as the resource
        """
        # The user is the owner, so it must be allowed
        self.assertTrue(
            authorized(TRANSFER, resource_owner=TestAuthorization.DN, env=self.env)
        )
        # The user belongs to the same vo, and transfer is set to vo, so it
        # must be allowed
        self.assertTrue(
            authorized(
                TRANSFER, resource_owner="someone", resource_vo="testvo", env=self.env
            )
        )
        # The resource belongs to a different user and vo, so it must
        # be forbidden
        self.assertFalse(
            authorized(
                TRANSFER, resource_owner="someone", resource_vo="othervo", env=self.env
            )
        )

    def test_authorized_same_dn_different_vo(self):
        """
        If the user is the owner of the resource, even if the DN does not match, it must be granted
        permissions.
        """
        self.assertTrue(
            authorized(
                TRANSFER,
                resource_owner=TestAuthorization.DN,
                resource_vo="othervo",
                env=self.env,
            )
        )

    def test_authorized_all(self):
        """
        Try to perform an action that is configured to be executed by anyone (all)
        """
        self.assertTrue(
            authorized(DELEGATION, resource_owner=TestAuthorization.DN, env=self.env)
        )
        self.assertTrue(
            authorized(
                DELEGATION, resource_owner="someone", resource_vo="testvo", env=self.env
            )
        )
        self.assertTrue(
            authorized(
                DELEGATION,
                resource_owner="someone",
                resource_vo="othervo",
                env=self.env,
            )
        )

    def test_authorize_decorator(self):
        """
        Make sure the decorators work
        """

        @authorize(TRANSFER, env=self.env)
        def func_allowed(a, b):
            return a == b

        @authorize(CONFIG, env=self.env)
        def func_forbidden(a, b):
            return a != b

        self.assertTrue(func_allowed(1, 1))
        self.assertRaises(Forbidden, func_forbidden, 0, 1)

    def test_authorize_config_via_db(self):
        """
        Credentials with no vo extensions, if the DN is in the database as authorized,
        configuration should be allowed
        """
        del self.creds
        del self.env["fts3.User.Credentials"]

        env = dict(GRST_CRED_AURI_0="dn:" + TestAuthorization.DN)
        self.creds = UserCredentials(env, TestAuthorization.ROLES)
        self.env["fts3.User.Credentials"] = self.creds

        self.assertFalse(authorized(CONFIG, env=self.env))

        authz = AuthorizationByDn(dn=TestAuthorization.DN, operation=CONFIG)
        Session.merge(authz)
        Session.commit()

        # Force reload of creds
        self.creds = UserCredentials(env, TestAuthorization.ROLES)
        self.env["fts3.User.Credentials"] = self.creds

        self.assertTrue(authorized(CONFIG, env=self.env))

    def test_authorize_root(self):
        """
        If the credentials are those of the server (hostcert.pem), then grant full
        access
        """
        env = dict()
        env["SSL_SERVER_S_DN"] = "/DN=test"

        env["GRST_CRED_AURI_0"] = "dn:/DN=notme"
        env["fts3.User.Credentials"] = UserCredentials(env, TestAuthorization.ROLES)
        self.assertFalse(authorized(CONFIG, env=env))
        self.assertTrue(authorized(DELEGATION, env=env))
        self.assertFalse(authorized(TRANSFER, env=env, resource_vo="atlas"))

        env["GRST_CRED_AURI_0"] = "dn:/DN=test"
        env["fts3.User.Credentials"] = UserCredentials(env, TestAuthorization.ROLES)
        self.assertTrue(authorized(CONFIG, env=env))
        self.assertTrue(authorized(DELEGATION, env=env))
        self.assertTrue(authorized(TRANSFER, env=env, resource_vo="atlas"))
