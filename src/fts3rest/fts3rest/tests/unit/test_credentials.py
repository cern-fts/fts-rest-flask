from fts3rest.lib.middleware.fts3auth.credentials import UserCredentials
from fts3rest.lib.middleware.fts3auth.constants import *
import unittest


class TestUserCredentials(unittest.TestCase):
    """
    Given a set of Gridsite environment variables, check the user
    credentials are being set correctly.
    """

    DN = "/DC=ch/DC=cern/CN=Test User"
    FQANS = [
        "/testvo/Role=NULL/Capability=NULL",
        "/testvo/group/Role=NULL/Capability=NULL",
        "/testvo/Role=myrole/Capability=NULL",
        "/testvo/Role=admin/Capability=NULL",
    ]

    ROLES = {"public": {"transfer": "vo", "deleg": ""}, "admin": {"config": "all"}}

    def test_basic_ssl(self):
        """
        Plain mod_ssl must work. No VO, though.
        """
        creds = UserCredentials({"SSL_CLIENT_S_DN": TestUserCredentials.DN})

        self.assertEqual(TestUserCredentials.DN, creds.user_dn)
        self.assertEqual([], creds.voms_cred)
        self.assertEqual(["TestUser@cern.ch"], creds.vos)

    def test_gridsite(self):
        """
        Set environment as mod_gridsite would do, and check the vos,
        roles and so on are set up properly.
        """
        env = {}
        env["GRST_CRED_AURI_0"] = "dn:" + TestUserCredentials.DN
        env["GRST_CRED_AURI_1"] = "fqan:" + TestUserCredentials.FQANS[0]
        env["GRST_CRED_AURI_2"] = "fqan:" + TestUserCredentials.FQANS[1]
        env["GRST_CRED_AURI_3"] = "fqan:" + TestUserCredentials.FQANS[2]
        env["GRST_CRED_AURI_4"] = "fqan:" + TestUserCredentials.FQANS[3]

        creds = UserCredentials(env)

        self.assertEqual(TestUserCredentials.DN, creds.user_dn)
        self.assertEqual(["testvo", "testvo/group"], creds.vos)
        self.assertEqual(TestUserCredentials.FQANS, creds.voms_cred)

        self.assertEqual(["myrole", "admin"], creds.roles)

    def test_default_roles(self):
        """
        Set environment as mod_gridsite would do, but with no roles
        present.
        """
        env = {}
        env["GRST_CRED_AURI_0"] = "dn:" + TestUserCredentials.DN
        env["GRST_CRED_AURI_1"] = "fqan:" + TestUserCredentials.FQANS[0]

        creds = UserCredentials(env, TestUserCredentials.ROLES)

        self.assertEqual(VO, creds.get_granted_level_for(TRANSFER))
        self.assertEqual(PRIVATE, creds.get_granted_level_for(DELEGATION))
        self.assertEqual(NONE, creds.get_granted_level_for(CONFIG))

    def test_roles(self):
        """
        Set environment as mod_gridsite would do, and then check that
        the granted levels are set up properly.
        """
        env = {}
        env["GRST_CRED_AURI_0"] = "dn:" + TestUserCredentials.DN
        env["GRST_CRED_AURI_1"] = "fqan:" + TestUserCredentials.FQANS[0]
        env["GRST_CRED_AURI_2"] = "fqan:" + TestUserCredentials.FQANS[1]
        env["GRST_CRED_AURI_3"] = "fqan:" + TestUserCredentials.FQANS[2]
        env["GRST_CRED_AURI_4"] = "fqan:" + TestUserCredentials.FQANS[3]

        creds = UserCredentials(env, TestUserCredentials.ROLES)

        self.assertEqual(ALL, creds.get_granted_level_for(CONFIG))
        self.assertEqual(VO, creds.get_granted_level_for(TRANSFER))
        self.assertEqual(PRIVATE, creds.get_granted_level_for(DELEGATION))
