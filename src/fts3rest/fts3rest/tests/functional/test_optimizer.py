from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3.model import Optimizer


class TestOptimizer(TestController):
    def setUp(self):
        super().setUp()
        self.setup_gridsite_environment()
        Session.query(Optimizer).delete()
        Session.commit()

    def test_set_optimizer_values(self):
        """
        Set optimizer values
        """

        resp = self.app.post_json(
            "/optimizer/current",
            params={
                "source_se": "test.cern.ch",
                "dest_se": "test2.cern.ch",
                "nostreams": 16,
                "active": 4096,
                "ema": 5,
            },
            status=200,
        ).json

        optimizer = Session.query(Optimizer).get(("test.cern.ch", "test2.cern.ch"))
        self.assertEqual("test.cern.ch", optimizer.source_se)
        self.assertEqual("test2.cern.ch", optimizer.dest_se)
        self.assertEqual(16, optimizer.nostreams)
        self.assertEqual(4096, optimizer.active)
        self.assertEqual(5, optimizer.ema)

    def test_wrong_optimizer_values(self):
        """
        Set wrong optimizer values
        """
        self.app.post_json(
            "/optimizer/current",
            params={
                "source_se": "test.cern.ch",
                "dest_se": "test2.cern.ch",
                "nostreams": 16,
                "active": -1,
            },
            status=400,
        )

        self.app.post_json(
            "/optimizer/current",
            params={"destination": "only-dest", "nostreams": 16,},
            status=400,
        )
        self.app.post_json(
            "/optimizer/current",
            params={
                "source_se": "test.cern.ch",
                "dest_se": "test2.cern.ch",
                "nostreams": -16,
            },
            status=400,
        )

    def test_reset_optimizer_values(self):
        """
        Reset a optmizer values
        """
        self.test_set_optimizer_values()
        resp = self.app.post_json(
            "/optimizer/current",
            params={
                "source_se": "test.cern.ch",
                "dest_se": "test2.cern.ch",
                "nostreams": 4,
                "active": 1024,
                "ema": 5,
            },
            status=200,
        ).json

        optimizer = Session.query(Optimizer).get(("test.cern.ch", "test2.cern.ch"))
        self.assertEqual("test.cern.ch", optimizer.source_se)
        self.assertEqual("test2.cern.ch", optimizer.dest_se)
        self.assertEqual(4, optimizer.nostreams)
        self.assertEqual(1024, optimizer.active)
        self.assertEqual(5, optimizer.ema)
