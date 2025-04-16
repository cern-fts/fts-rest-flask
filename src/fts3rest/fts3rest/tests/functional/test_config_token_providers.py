from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import TokenProvider


class TestConfigTokenProviders(TestController):
    def setUp(self):
        super(TestConfigTokenProviders, self).setUp()
        self.setup_gridsite_environment()
        Session.query(TokenProvider).delete()
        Session.commit()

    def tearDown(self):
        Session.query(TokenProvider).delete()
        Session.commit()
        super(TestConfigTokenProviders, self).tearDown()

    def _compare_token_provider(self, expected):
        providers = self.app.get(url="/config/token_providers", status=200).json
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0], expected)

    def test_retrieve_token_providers(self):
        """
        Retrieve token providers config
        """
        Session.execute(
            "INSERT INTO "
            "t_token_provider(name, issuer, client_id, client_secret, required_submission_scope, vo_mapping) "
            "VALUES('dteam', 'https://dteam-auth.cern.ch/', 'client_id', 'client_secret', 'fts', 'dteam');"
        )

        self._compare_token_provider(
            {
                "name": "dteam",
                "issuer": "https://dteam-auth.cern.ch/",
                "client_id": "client_id",
                "client_secret": "client_secret",
                "required_submission_scope": "fts",
                "vo_mapping": "dteam",
            }
        )

    def test_insert_token_provider(self):
        """
        Insert token provider configuration
        """
        self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                issuer="https://dteam-auth.cern.ch",  # Notice missing trailing '/'
                client_id="client_id",
                client_secret="client_secret",
            ),
            status=200,
        )

        self._compare_token_provider(
            {
                "name": "dteam",
                "issuer": "https://dteam-auth.cern.ch/",
                "client_id": "client_id",
                "client_secret": "client_secret",
                "required_submission_scope": None,
                "vo_mapping": None,
            }
        )

    def test_set_token_provider(self):
        """
        Update existing token provider configuration
        """
        Session.execute(
            "INSERT INTO "
            "t_token_provider(name, issuer, client_id, client_secret, required_submission_scope, vo_mapping) "
            "VALUES('dteam', 'https://dteam-auth.cern.ch/', 'client_id', 'client_secret', 'fts', 'dteam');"
        )
        self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam_updated",
                issuer="https://dteam-auth.cern.ch/",
                client_id="client_id_updated",
                client_secret="client_secret_updated",
            ),
            status=200,
        )

        self._compare_token_provider(
            {
                "name": "dteam_updated",
                "issuer": "https://dteam-auth.cern.ch/",
                "client_id": "client_id_updated",
                "client_secret": "client_secret_updated",
                "required_submission_scope": None,
                "vo_mapping": None,
            }
        )

    def test_set_token_provider_invalid(self):
        """
        Set invalid token provider configuration
        """

        # Missing name
        message = self.app.post_json(
            url="/config/token_providers",
            params=dict(
                issuer="dteam-auth.cern.ch",
                client_id="client_id",
                client_secret="client_secret",
            ),
            status=400,
        ).json["message"]
        self.assertTrue(all(s in message.lower() for s in ["missing", "name"]))

        # Missing Issuer
        message = self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                client_id="client_id",
                client_secret="client_secret",
            ),
            status=400,
        ).json["message"]
        self.assertTrue(all(s in message.lower() for s in ["missing", "issuer"]))

        # Invalid Issuer
        message = self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                issuer="dteam-auth.cern.ch",
                client_id="client_id",
                client_secret="client_secret",
            ),
            status=400,
        ).json["message"]
        self.assertTrue(all(s in message.lower() for s in ["invalid", "issuer"]))

        # Missing Client ID
        message = self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                issuer="https://dteam-auth.cern.ch/",
                client_secret="client_secret",
            ),
            status=400,
        ).json["message"]
        self.assertTrue(all(s in message.lower() for s in ["missing", "client id"]))

        # Missing Client Secret
        message = self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                issuer="https://dteam-auth.cern.ch/",
                client_id="client_id",
            ),
            status=400,
        ).json["message"]
        self.assertTrue(all(s in message.lower() for s in ["missing", "client secret"]))

    def test_remove_token_provider(self):
        """
        Remove token provider from the configuration
        """
        self.app.post_json(
            url="/config/token_providers",
            params=dict(
                name="dteam",
                issuer="https://dteam-auth.cern.ch/",
                client_id="client_id",
                client_secret="client_secret",
            ),
            status=200,
        )

        self._compare_token_provider(
            {
                "name": "dteam",
                "issuer": "https://dteam-auth.cern.ch/",
                "client_id": "client_id",
                "client_secret": "client_secret",
                "required_submission_scope": None,
                "vo_mapping": None,
            }
        )

        self.app.delete(
            url="/config/token_providers/dteam",
            status=204,
        )

        providers = self.app.get(
            url="/config/token_providers",
            status=200,
        ).json

        self.assertEqual(len(providers), 0)
