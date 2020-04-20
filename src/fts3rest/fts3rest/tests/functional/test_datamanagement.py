from fts3rest.tests import TestController
from unittest import SkipTest


class TestDatamanagement(TestController):
    """
    Tests for user and storage banning
    """

    def setUp(self):
        try:
            import gfal2
        except ImportError:
            raise SkipTest("Failed to import gfal2")
        super().setUp()
        self.setup_gridsite_environment()

    def test_get_list(self):
        """
        Try list the content of a remote directory
        """
        self.push_delegation()
        response = self.app.get(
            url="/dm/list",
            params={
                "surl": "mock://destination.es/file?list=a:1755:0,b:0755:123,c:000:0,d:0444:1234",
                "size": 1,
                "mode": 0o775,
                "mtime": 5,
            },
            status=200,
        ).json
        self.assertIn("a", response)
        self.assertIn("b", response)
        self.assertIn("c", response)
        self.assertIn("d", response)
        self.assertEqual(123, response["b"]["size"])

    def test_missing_surl(self):
        """
        Try list the content of a remote directory
        """
        self.push_delegation()
        self.app.get(url="/dm/list?size=1&mode=0755&mtime=5", status=400)

    def test_get_stat(self):
        """
        Try stat a remote file
        """
        self.push_delegation()
        self.app.get(
            url="/dm/stat",
            params={
                "surl": "mock://destination.es/file",
                "mode": 1,
                "nlink": 1,
                "size": 1,
                "atime": 1,
                "mtime": 1,
                "ctime": 1,
            },
            status=200,
        )

    def test_rename(self):
        """
        Try to rename
        """
        self.push_delegation()
        self.app.post(
            url="/dm/rename",
            params={
                "surl": "mock://destination.es/file3",
                "mode": 0o775,
                "nlink": 1,
                "size": 1,
                "atime": 1,
                "mtime": 1,
                "ctime": 1,
            },
            status=400,
        )

    def test_unlink(self):
        """
        Try to unlink
        """
        self.push_delegation()
        self.app.post(
            url="/dm/unlink",
            params={
                "surl": "mock://destination.es/file3",
                "size": 1,
                "mode": 5,
                "mtime": 5,
            },
            status=400,
        )

    def test_rmdir(self):
        """
        Try to rmdir
        """
        self.push_delegation()
        self.app.post(
            url="/dm/rmdir",
            params={
                "surl": "mock://destination.es/file3",
                "mode": 0o775,
                "nlink": 1,
                "size": 1,
                "atime": 1,
                "mtime": 1,
                "ctime": 1,
            },
            status=400,
        )

    def test_mkdir(self):
        """
        Try to mkdir
        """
        self.push_delegation()
        self.app.post(
            url="/dm/mkdir",
            params={
                "surl": "mock://destination.es/file3",
                "mode": 0o775,
                "nlink": 1,
                "size": 1,
                "atime": 1,
                "mtime": 1,
                "ctime": 1,
            },
            status=400,
        )
