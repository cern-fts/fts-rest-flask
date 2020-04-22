from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3.model.config import (
    ConfigAudit,
    ServerConfig,
    OperationConfig,
    ShareConfig,
    LinkConfig,
)


class TestConfigShares(TestController):
    def setUp(self):
        super(TestConfigShares, self).setUp()
        self.setup_gridsite_environment()
        Session.query(LinkConfig).delete()
        Session.query(ShareConfig).delete()
        Session.query(ServerConfig).delete()
        Session.query(ConfigAudit).delete()
        Session.query(OperationConfig).delete()
        Session.execute(
            "INSERT INTO "
            "t_link_config(source_se, dest_se, symbolic_name,"
            " min_active, max_active, optimizer_mode, nostreams)"
            " VALUES('*', '*', '*', 2, 130, 2, 0);"
        )
        Session.commit()

    def tearDown(self):
        Session.query(LinkConfig).delete()
        Session.query(ShareConfig).delete()
        Session.query(ServerConfig).delete()
        Session.query(ConfigAudit).delete()
        Session.query(OperationConfig).delete()
        Session.commit()
        super(TestConfigShares, self).tearDown()

    def test_set_share(self):
        """
        Set up shares config
        """
        self.app.post_json(
            url="/config/shares",
            params=dict(
                source="gsiftp://source",
                destination="gsiftp://nowhere",
                vo="dteam",
                share=80,
            ),
            status=200,
        )

    def test_wrong_config_shares0(self):
        """
        Test wrong value for share in params
        """
        self.app.post_json(
            url="/config/shares",
            params=dict(
                source="gsiftp://source",
                destination="gsiftp://nowhere",
                vo="dteam",
                share="dfdf",
            ),
            status=400,
        )

    def test_wrong_config_shares1(self):
        """
        Test missing one of params
        """
        config = {
            "source": "gsiftp://source",
            "destination": "gsiftp://nowhere",
            "vo": "dteam",
            "share": 80,
        }

        for i in config:
            k = config
            k[i] = ""
            self.app.post_json(url="/config/shares", params=k, status=400)
            return config

    def test_wrong_config_shares2(self):
        """
        Test wrong source or destination
        """
        self.app.post_json(
            url="/config/shares",
            params=dict(
                source="dfgsdfsg", destination="gsiftp://nowhere", vo="dteam", share=80
            ),
            status=400,
        )

        self.app.post_json(
            url="/config/shares",
            params=dict(
                source="gsiftp://source", destination="klhjkhjk", vo="dteam", share=80
            ),
            status=400,
        )

    def test_get_share_config(self):
        """
        Get shares config
        """
        self.test_set_share()
        self.app.get(url="/config/shares", status=200)

    def test_remove_share(self):
        """
        Try to remove shares
        """
        self.app.delete(
            url="/config/shares?share=80&destination=gsiftp://nowhere&vo=dteam",
            status=400,
        )
        self.app.delete(
            url="/config/shares?share=80&destination=gsiftp://nowhere&vo=dteam&source=gsiftp://source",
            status=204,
        )
