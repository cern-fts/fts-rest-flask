from datetime import datetime

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import ConfigAudit, Host


class TestDrain(TestController):
    def setUp(self):
        super(TestDrain, self).setUp()
        self.setup_gridsite_environment()

        Session.add(
            Host(
                hostname="host1.cern.ch",
                service_name="fts3",
                beat=datetime.utcnow(),
                drain=False,
            )
        )
        Session.add(
            Host(
                hostname="host1.cern.ch",
                service_name="bringonline",
                beat=datetime.utcnow(),
                drain=False,
            )
        )
        Session.add(
            Host(
                hostname="host2.cern.ch",
                service_name="fts3",
                beat=datetime.utcnow(),
                drain=False,
            )
        )
        Session.add(
            Host(
                hostname="host2.cern.ch",
                service_name="bringonline",
                beat=datetime.utcnow(),
                drain=False,
            )
        )

        Session.commit()

    def tearDown(self):
        Session.query(ConfigAudit).delete()
        Session.query(Host).delete()
        Session.commit()
        super(TestDrain, self).tearDown()

    def test_get(self):
        """
        Test getting the hosts and their drain status
        """
        response = self.app.get_json(url="/config", status=200).json

        self.assertEqual(5, len(response))

        hosts = [e["hostname"] for e in response]
        self.assertIn("host1.cern.ch", hosts)
        self.assertIn("host2.cern.ch", hosts)

        services = [e["service_name"] for e in response]
        self.assertIn("fts3", services)
        self.assertIn("bringonline", services)

        for entry in response:
            self.assertFalse(entry["drain"])

        self.assertEqual(0, len(Session.query(ConfigAudit).all()))

    def test_set_drain(self):
        """
        Set one host to drain
        """
        self.app.post_json(
            url="/config/drain",
            params=dict(hostname="host1.cern.ch", drain=True),
            status=200,
        )

        hosts = Session.query(Host).all()
        for host in hosts:
            if host.hostname == "host1.cern.ch":
                self.assertTrue(host.drain)
            else:
                self.assertFalse(host.drain)

        response = self.app.get_json(url="/config", status=200).json
        for entry in response:
            if entry["hostname"] == "host1.cern.ch":
                self.assertTrue(entry["drain"])
            else:
                self.assertFalse(entry["drain"])

        self.assertEqual(1, len(Session.query(ConfigAudit).all()))

    def test_set_invalid_drain(self):
        """
        Set to drain, but an invalid value
        """
        self.app.post_json(
            url="/config/drain",
            params=dict(hostname="host1.cern.ch", drain="xxxx"),
            status=400,
        )

        self.assertEqual(0, len(Session.query(ConfigAudit).all()))

    def test_set_undrain(self):
        """
        Set to undrain
        """
        self.test_set_drain()

        self.app.post_json(
            url="/config/drain",
            params=dict(hostname="host1.cern.ch", drain=False),
            status=200,
        )

        hosts = Session.query(Host).all()
        for host in hosts:
            self.assertFalse(host.drain)

        response = self.app.get_json(url="/config", status=200).json
        for entry in response:
            self.assertFalse(entry["drain"])

        self.assertEqual(2, len(Session.query(ConfigAudit).all()))
