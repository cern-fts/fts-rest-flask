from fts3rest.tests import TestController
import unittest


class TestOptions(TestController):
    """
    Tests for the OPTIONS method
    """

    def assertCountEqual(self, first, second, msg=...) -> None:
        second = set(second)
        second.discard("HEAD")
        super().assertCountEqual(first, second)

    def test_options_whoami(self):
        """
        Test OPTIONS on whoami
        """
        self.setup_gridsite_environment()

        response = self.app.options("/whoami", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

        response = self.app.options("/whoami/certificate", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

    def test_options_ban(self):
        """
        Test OPTIONS on ban urls
        """
        self.setup_gridsite_environment()

        response = self.app.options("/ban/se", status=200)
        self.assertCountEqual(["POST", "GET", "OPTIONS", "DELETE"], response.allow)

        response = self.app.options("/ban/dn", status=200)
        self.assertCountEqual(["POST", "GET", "OPTIONS", "DELETE"], response.allow)

    @unittest.skip(
        "Flask bug when static static_url_path='', OPTIONS always returns GET"
    )
    def test_options_dm(self):
        """
        Test OPTIONS on data management urls
        """
        self.setup_gridsite_environment()

        # Methods for modifications
        for path in ["/dm/unlink", "/dm/rename", "/dm/rmdir", "/dm/mkdir"]:
            response = self.app.options(path, status=200)
            self.assertCountEqual(["POST", "OPTIONS"], response.allow)

        # Methods for querying
        for path in ["/dm/stat", "/dm/list"]:
            response = self.app.options(path, status=200)
            self.assertCountEqual(["GET", "OPTIONS"], response.allow)

    def test_options_jobs(self):
        """
        Test OPTIONS on job urls
        """
        self.setup_gridsite_environment()

        response = self.app.options("/jobs", status=200)
        self.assertCountEqual(["GET", "POST", "PUT", "OPTIONS"], response.allow)

        response = self.app.options("/jobs/1234-56789", status=200)
        self.assertCountEqual(["GET", "DELETE", "POST", "OPTIONS"], response.allow)

        response = self.app.options("/jobs/1234-56789/files", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

    @unittest.skip(
        "Flask bug when static static_url_path='', OPTIONS always returns GET"
    )
    def test_options_delegation(self):
        """
        Test OPTIONS on delegation urls
        """
        self.setup_gridsite_environment()

        response = self.app.options("/delegation", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

        response = self.app.options("/delegation/1234", status=200)
        self.assertCountEqual(["GET", "DELETE", "OPTIONS"], response.allow)

        response = self.app.options("/delegation/1234/request", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

        response = self.app.options("/delegation/1234/credential", status=200)
        self.assertCountEqual(["POST", "PUT", "OPTIONS"], response.allow)

    def test_options_optimizer(self):
        """
        Test OPTIONS on optimizer urls
        """
        self.setup_gridsite_environment()

        response = self.app.options("/optimizer", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

        response = self.app.options("/optimizer/evolution", status=200)
        self.assertCountEqual(["GET", "OPTIONS"], response.allow)

        response = self.app.options("/optimizer/current", status=200)
        self.assertCountEqual(["GET", "POST", "OPTIONS"], response.allow)

    @unittest.skip(
        "Flask bug when static static_url_path='', OPTIONS always returns GET"
    )
    def test_options_404(self):
        """
        Test OPTIONS on a non-existing url
        """
        self.setup_gridsite_environment()

        self.app.options("/thiswouldreallysurpriseme", status=404)

    def test_entry_point(self):
        """
        Test main entry point
        """
        self.setup_gridsite_environment()

        json_response = self.app.get("/", status=200).json
        self.assertIn("api", json_response)
