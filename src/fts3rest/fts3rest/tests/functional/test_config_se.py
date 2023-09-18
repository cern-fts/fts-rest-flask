from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import ConfigAudit, Optimizer, OperationConfig, Se


class TestConfigSe(TestController):
    def setUp(self):
        super(TestConfigSe, self).setUp()
        self.setup_gridsite_environment()
        Session.query(Optimizer).delete()
        Session.query(ConfigAudit).delete()
        Session.query(OperationConfig).delete()
        Session.query(Se).delete()
        Session.commit()
        self.host_config = {
            "operations": {
                "atlas": {
                    "delete": 22,
                    "staging": 32,
                },
                "dteam": {"delete": 10, "staging": 11},
            },
            "se_info": {
                "ipv6": 1,
                "outbound_max_active": 55,
                "inbound_max_active": 11,
                "inbound_max_throughput": 33,
                "se_metadata": "metadata",
            },
        }

    def tearDown(self):
        Session.query(Optimizer).delete()
        Session.query(ConfigAudit).delete()
        Session.query(OperationConfig).delete()
        Session.query(Se).delete()
        Session.commit()
        super(TestConfigSe, self).tearDown()

    def test_set_se_config(self):
        """
        Set SE config
        """
        config = {"test.cern.ch": self.host_config}
        self.app.post_json("/config/se", params=config, status=200)

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(2, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(4, len(ops))
        for op in ops:
            self.assertEqual(
                config[op.host]["operations"][op.vo_name][op.operation],
                op.concurrent_ops,
            )

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").first()
        self.assertEqual(1, se.ipv6)
        self.assertEqual(55, se.outbound_max_active)
        self.assertEqual(11, se.inbound_max_active)
        self.assertEqual(33, se.inbound_max_throughput)

    def test_set_se_config_bad_name(self):
        """
        Set SE config with invalid storage names
        """
        for storage_name in (" ", "", "\n", "\t"):
            config = {storage_name: self.host_config}

            self.app.post_json("/config/se", params=config, status=400)

            audits = Session.query(ConfigAudit).all()
            self.assertEqual(0, len(audits))

            ops = (
                Session.query(OperationConfig)
                .filter(OperationConfig.host == storage_name)
                .all()
            )
            self.assertEqual(0, len(ops))

            se = Session.query(Se).filter(Se.storage == storage_name).all()
            self.assertEqual(0, len(se))

    def test_reset_se_config(self):
        """
        Reset SE config
        """
        self.test_set_se_config()

        config = {
            "test.cern.ch": {
                "operations": {
                    "atlas": {
                        "delete": 1,
                        "staging": 2,
                    },
                    "dteam": {"delete": 3, "staging": 4},
                },
                "se_info": {
                    "ipv6": 0,
                    "outbound_max_active": 88,
                    "inbound_max_active": 11,
                    "inbound_max_throughput": 10,
                },
            }
        }
        self.app.post_json("/config/se", params=config, status=200)

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(4, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(4, len(ops))
        for op in ops:
            self.assertEqual(
                config[op.host]["operations"][op.vo_name][op.operation],
                op.concurrent_ops,
            )

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").first()
        self.assertEqual(0, se.ipv6)
        self.assertEqual(88, se.outbound_max_active)
        self.assertEqual(11, se.inbound_max_active)
        self.assertEqual(10, se.inbound_max_throughput)

    def test_get_se_config(self):
        """
        Get SE config
        """
        self.test_set_se_config()

        cfg = self.app.get_json("/config/se?se=test.cern.ch", status=200).json

        self.assertIn("test.cern.ch", cfg.keys())
        se_cfg = cfg["test.cern.ch"]

        self.assertIn("operations", se_cfg.keys())
        self.assertIn("se_info", se_cfg.keys())

        self.assertEqual(
            {
                "atlas": {"delete": 22, "staging": 32},
                "dteam": {"delete": 10, "staging": 11},
            },
            se_cfg["operations"],
        )

        self.assertEqual(1, se_cfg["se_info"]["ipv6"])
        self.assertEqual(55, se_cfg["se_info"]["outbound_max_active"])
        self.assertEqual(11, se_cfg["se_info"]["inbound_max_active"])
        self.assertEqual(33, se_cfg["se_info"]["inbound_max_throughput"])

    def test_remove_se_config(self):
        """
        Remove the configuration for a given SE
        """
        self.test_get_se_config()
        self.app.delete(url="/config/se", status=400)
        self.app.delete(url="/config/se?se=test.cern.ch", status=204)

    def test_set_se_config_empty(self):
        """
        Set SE config with an empty se_info JSON;
        Only the operations should be configured and the se configuration should not be created
        """
        config = {
            "test.cern.ch": {
                "operations": {
                    "atlas": {
                        "delete": 22,
                        "staging": 32,
                    },
                    "dteam": {"delete": 10, "staging": 11},
                },
                "se_info": {},
            }
        }
        self.app.post_json("/config/se", params=config, status=200)

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(1, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(4, len(ops))
        for op in ops:
            self.assertEqual(
                config[op.host]["operations"][op.vo_name][op.operation],
                op.concurrent_ops,
            )

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").first()
        self.assertIsNone(se)

    def test_set_operations_config_empty(self):
        """
        Set SE config with an empty operations JSON;
        Only the se_info should be configured and the operations configuration should not be created
        """
        config = {
            "test.cern.ch": {
                "operations": {},
                "se_info": {
                    "ipv6": 1,
                    "outbound_max_active": 88,
                    "inbound_max_active": 11,
                    "inbound_max_throughput": 10,
                },
            }
        }
        self.app.post_json("/config/se", params=config, status=200)

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(1, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(0, len(ops))

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").first()
        self.assertEqual(1, se.ipv6)
        self.assertEqual(88, se.outbound_max_active)
        self.assertEqual(11, se.inbound_max_active)
        self.assertEqual(10, se.inbound_max_throughput)

    def test_set_se_invalid_values(self):
        """
        Set SE config with invalid values
        """
        config = {
            "test.cern.ch": {
                "se_info": {
                    "ipv6": "invalid",
                    "outbound_max_active": 88,
                    "inbound_max_active": 11,
                    "inbound_max_throughput": 10,
                },
            }
        }
        response = self.app.post_json("/config/se", params=config, status=400)

        self.assertEqual("Field ipv6 is expected to be int", response.json["message"])

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(0, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(0, len(ops))

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").all()
        self.assertEqual(0, len(se))

    def test_set_operation_invalid_values(self):
        """
        Set SE config with invalid values
        """
        config = {
            "test.cern.ch": {
                "operations": {
                    "atlas": {
                        "delete": 22,
                        "staging": 32,
                    },
                    "dteam": {"staging": "invalid"},
                },
            }
        }
        response = self.app.post_json("/config/se", params=config, status=400)

        self.assertEqual(
            "Field concurrent_ops is expected to be int", response.json["message"]
        )

        audits = Session.query(ConfigAudit).all()
        self.assertEqual(0, len(audits))

        ops = (
            Session.query(OperationConfig)
            .filter(OperationConfig.host == "test.cern.ch")
            .all()
        )
        self.assertEqual(0, len(ops))

        se = Session.query(Se).filter(Se.storage == "test.cern.ch").all()
        self.assertEqual(0, len(se))
