from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import ConfigAudit, AuthorizationByDn


class TestConfigAuthz(TestController):
    def setUp(self):
        super(TestConfigAuthz, self).setUp()
        self.setup_gridsite_environment()
        Session.query(AuthorizationByDn).delete()
        Session.query(ConfigAudit).delete()
        Session.commit()

    def tearDown(self):
        Session.query(AuthorizationByDn).delete()
        Session.query(ConfigAudit).delete()
        Session.commit()
        super().tearDown()

    def _add_admin_level_authz(self, dn):
        authz = AuthorizationByDn()
        authz.dn = dn
        authz.operation = "admin"
        Session.add(authz)
        Session.commit()

    def test_add_authz(self):
        """
        Add a new operation for a new dn
        """
        self.app.post_json(
            "/config/authorize",
            params={"dn": "/DN=a.test.user", "operation": "config"},
            status=200,
        )

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(1, len(audits))

        authz = Session.query(AuthorizationByDn).get(("/DN=a.test.user", "config"))
        self.assertIsNotNone(authz)

    def test_remove_authz(self):
        """
        Remove a operation for a dn
        """
        self.test_add_authz()
        self.app.delete(
            "/config/authorize?dn=/DN=a.test.user&operation=config", status=204
        )

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(2, len(audits))

        authz = Session.query(AuthorizationByDn).get(("/DN=a.test.user", "config"))
        self.assertEqual(None, authz)

    def test_list_authz(self):
        """
        List special authorizations
        """
        self.test_add_authz()
        authz = self.app.get_json("/config/authorize", status=200).json

        self.assertEqual(1, len(authz))
        self.assertEqual(authz[0]["dn"], "/DN=a.test.user")
        self.assertEqual(authz[0]["operation"], "config")

    def test_add_authz_miss_dn_or_op(self):
        """
        Miss dn or op
        """
        config = {"dn": "/DN=a.test.user", "operation": "config"}

        for i in config:
            k = config
            k[i] = ""
            self.app.post(url="/config/authorize", params=k, status=400)
            return config

    def test_add_authz_admin_level(self):
        """
        Add DN with admin level.
        Should return a BadRequest response
        """
        self.app.post_json(
            url="/config/authorize",
            params={"dn": "/DN=a.test.user", "operation": "admin"},
            status=400,
        )

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(0, len(audits))

        authz = Session.query(AuthorizationByDn).get(("/DN=a.test.user", "admin"))
        self.assertIsNone(authz)

    def test_list_authz_missing_dn_or_op(self):
        """
        List missing dn or op
        """
        self.app.get("/config/authorize?operation=config", status=200)
        self.app.get("/config/authorize?dn=/DN=a.test.user", status=200)

    def test_remove_authz_wrong(self):
        """
        Remove with missing dn or op
        """
        self.test_add_authz()
        self.app.delete("/config/authorize?operation=config", status=400)
        self.app.delete("/config/authorize?dn=/DN=a.test.user", status=204)

    def test_remove_authz_admin_level(self):
        """
        Attempt to remove DN with admin operation.
        Should return a BadRequest response
        """
        self._add_admin_level_authz("/DN=a.test.user")
        self.app.delete(
            "/config/authorize?dn=/DN=a.test.user&operation=admin", status=400
        )

    def test_remove_authz_admin_level_excluded(self):
        """
        When removing all authorizations for a given DN,
        admin level should be excluded
        """
        self.test_add_authz()
        self._add_admin_level_authz("/DN=a.test.user")

        authz = self.app.get_json("/config/authorize", status=200).json
        self.assertEqual(2, len(authz))

        self.app.delete("/config/authorize?dn=/DN=a.test.user", status=204)
        authz = self.app.get_json("/config/authorize", status=200).json

        self.assertEqual(1, len(authz))
        self.assertEqual(authz[0]["dn"], "/DN=a.test.user")
        self.assertEqual(authz[0]["operation"], "admin")
