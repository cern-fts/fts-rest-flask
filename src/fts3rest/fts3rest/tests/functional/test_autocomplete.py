from fts3rest.tests import TestController


class TestAutocomplete(TestController):
    """
    Tests for autocompleting
    """

    def setUp(self):
        super().setUp()
        self.setup_gridsite_environment()

    def test_autocomplete_dn(self):
        """
        Test autocomplete dn
        """
        autocomp = self.app.get(
            url="/autocomplete/dn",
            params={"user_dn": "/DC=cern", "message": "term"},
            status=200,
        ).json
        self.assertEqual(0, len(autocomp))

    def test_autocomplete_source(self):
        """
        Test autocomplete source
        """
        autocomp = self.app.get(
            url="/autocomplete/source",
            params={"source": "srm://", "message": "term"},
            status=200,
        ).json
        self.assertEqual(0, len(autocomp))

    def test_autocomplete_destination(self):
        """
        Test autocomplete destination
        """
        autocomp = self.app.get(
            url="/autocomplete/destination",
            params={"destination": "srm://", "message": "term"},
            status=200,
        ).json
        self.assertEqual(0, len(autocomp))

    def test_autocomplete_storage(self):
        """
        Test autocomplete storage
        """
        autocomp = self.app.get(
            url="/autocomplete/storage",
            params={"storage": "srm://", "message": "term"},
            status=200,
        ).json
        self.assertEqual(0, len(autocomp))

    def test_autocomplete_vo(self):
        """
        Test autocomplete vo
        """
        autocomp = self.app.get(
            url="/autocomplete/vo",
            params={"vo": "srm://", "message": "term"},
            status=200,
        ).json
        self.assertEqual(0, len(autocomp))
