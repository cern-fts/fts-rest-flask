from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import ConfigAudit, ServerConfig


class TestConfigGlobal(TestController):
    def setUp(self):
        super(TestConfigGlobal, self).setUp()
        self.setup_gridsite_environment()
        Session.query(ServerConfig).delete()
        Session.query(ConfigAudit).delete()
        Session.commit()

    def tearDown(self):
        Session.query(ServerConfig).delete()
        Session.query(ConfigAudit).delete()
        Session.commit()
        super().tearDown()

    def test_set(self):
        """
        Set the number of retries per VO and also globally
        """
        self.app.post_json(
            url="/config/global",
            params=dict(
                retry=42,
                max_time_queue=22,
                global_timeout=55,
                sec_per_mb=1,
                show_user_dn=True,
                vo_name="dteam",
            ),
            status=200,
        )

        config = Session.query(ServerConfig).get("dteam")
        self.assertEqual(42, config.retry)
        audit = Session.query(ConfigAudit).all()
        self.assertEqual(1, len(audit))

    def test_reset(self):
        """
        Set once, reset new values
        """
        self.test_set()
        self.app.post_json(
            url="/config/global", params=dict(retry=55, vo_name="dteam"), status=200
        )

        config = Session.query(ServerConfig).get("dteam")
        self.assertEqual(55, config.retry)

        audit = Session.query(ConfigAudit).all()
        self.assertEqual(2, len(audit))

    def test_reset_and_add(self):
        """
        Set, reset, add a new one
        """
        self.test_reset()

        self.app.post_json(
            url="/config/global",
            params=dict(
                retry=42,
                max_time_queue=22,
                global_timeout=55,
                sec_per_mb=1,
                show_user_dn=True,
                vo_name="atlas",
            ),
            status=200,
        )

        config = Session.query(ServerConfig).get("atlas")
        self.assertIsNotNone(config)
        config = Session.query(ServerConfig).get("dteam")
        self.assertIsNotNone(config)

        audit = Session.query(ConfigAudit).all()
        self.assertEqual(3, len(audit))

    def test_set_invalid_value(self):
        """
        Try to set something with an invalid value
        """
        self.app.post_json(
            url="/config/global",
            params=dict(
                retry="this should be an integer",
                max_time_queue=22,
                global_timeout=55,
                sec_per_mb=1,
                show_user_dn=True,
                vo_name="atlas",
            ),
            status=400,
        )

    def test_delete_vo_global_config(self):
        """
        Delete the global configuration for the given VO
        """
        self.test_set()

        self.app.delete(url="/config/global", status=400)
        self.app.delete(url="/config/global?vo_name=dteam", status=204)
        vo_name = Session.query(ServerConfig).get("dteam")
        self.assertIsNone(vo_name)
