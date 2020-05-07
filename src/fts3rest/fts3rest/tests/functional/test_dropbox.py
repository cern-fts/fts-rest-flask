from unittest.mock import patch

from fts3rest.model.meta import Session
from fts3rest.tests import TestController
from fts3rest.controllers.CSdropbox import DropboxConnector
from fts3rest.model import CloudStorage, CloudStorageUser


def _oauth_header_dict(raw_header):
    parts = [h.strip() for h in raw_header[6:].split(",")]
    d = dict()
    for p in parts:
        k, v = p.split("=", 2)
        d[k] = v
    return d


def _mocked_dropbox_make_call(self, command_url, auth_headers, parameters):
    assert command_url.startswith("https://api.dropbox.com/")
    assert auth_headers.startswith("OAuth ")

    oauth_headers = _oauth_header_dict(auth_headers)

    command_path = command_url[23:]
    if command_path == "/1/oauth/request_token":
        assert oauth_headers["oauth_consumer_key"] == '"1234"'
        assert oauth_headers["oauth_signature"] == '"sssh&"'
        return "oauth_token_secret=1234&oauth_token=abcd"
    elif command_path == "/1/oauth/access_token":
        assert oauth_headers["oauth_consumer_key"] == '"1234"'
        assert oauth_headers["oauth_signature"] == '"sssh&1234"'
        return "oauth_token_secret=blahblahsecret&oauth_token=cafesilvousplait"
    else:
        return "404 Not Found"


class TestDropbox(TestController):
    """
    Tests dropbox api
    """

    def setUp(self):
        super(TestDropbox, self).setUp()
        # Monkey-patch the controller as to be us who answer :)
        Session.query(CloudStorageUser).delete()
        Session.query(CloudStorage).delete()
        Session.commit()
        # Inject a Dropbox app
        cs = CloudStorage(
            storage_name="DROPBOX",
            app_key="1234",
            app_secret="sssh",
            service_api_url="https://api.dropbox.com",
        )
        Session.merge(cs)
        Session.commit()
        self.setup_gridsite_environment()

    def tearDown(self):
        Session.query(CloudStorageUser).delete()
        Session.query(CloudStorage).delete()
        Session.commit()
        super(TestDropbox, self).tearDown()

    @patch.object(DropboxConnector, "_make_call", new=_mocked_dropbox_make_call)
    def test_loaded(self):
        """
        Just test if the Dropbox plugin has been loaded
        Should be, in a development environment!
        """
        is_registered = self.app.get(url="/cs/registered/dropbox", status=200).json
        self.assertFalse(is_registered)

    @patch.object(DropboxConnector, "_make_call", new=_mocked_dropbox_make_call)
    def test_request_access(self):
        """
        Request a 'request' token
        """
        self.app.get(url="/cs/access_request/dropbox", status=404)

        response = self.app.get(url="/cs/access_request/dropbox/request", status=200)
        self.assertEqual(
            "oauth_token_secret=1234&oauth_token=abcd", response.data.decode()
        )

        csu = Session.query(CloudStorageUser).get(
            ("/DC=ch/DC=cern/CN=Test User", "DROPBOX", "")
        )
        self.assertTrue(csu is not None)
        self.assertEqual("abcd", csu.request_token)
        self.assertEqual("1234", csu.request_token_secret)

    @patch.object(DropboxConnector, "_make_call", new=_mocked_dropbox_make_call)
    def test_access_granted_no_request(self):
        """
        Access grant without a request must fail
        """
        self.app.get(url="/cs/access_grant/dropbox", status=400)

    @patch.object(DropboxConnector, "_make_call", new=_mocked_dropbox_make_call)
    def test_access_granted(self):
        """
        Get a request token and grant access
        """
        self.app.get(url="/cs/access_request/dropbox", status=404)
        self.app.get(url="/cs/access_request/dropbox/request", status=200)
        self.app.get(url="/cs/access_grant/dropbox", status=200)

        csu = Session.query(CloudStorageUser).get(
            ("/DC=ch/DC=cern/CN=Test User", "DROPBOX", "")
        )
        self.assertTrue(csu is not None)
        self.assertEqual("cafesilvousplait", csu.access_token)
        self.assertEqual("blahblahsecret", csu.access_token_secret)

    @patch.object(DropboxConnector, "_make_call", new=_mocked_dropbox_make_call)
    def test_delete_token(self):
        """
        Remove the stored token
        """
        self.test_access_granted()
        self.app.delete(url="/cs/access_grant/dropbox", status=204)

        csu = Session.query(CloudStorageUser).get(
            ("/DC=ch/DC=cern/CN=Test User", "DROPBOX", "")
        )
        self.assertTrue(csu is None)
