import json

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import Job, DataManagement
import unittest


class TestJobDeletion(TestController):
    """
    Test DELETE jobs
    """

    @unittest.skip(
        "Deleting jobs in FTS are being decommissioned. Tests should be removed in the future."
    )
    def test_simple_delete(self):
        """
        Simple deletion job
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "delete": [
                "root://source.es/file",
                {"surl": "root://source.es/file2", "metadata": {"a": "b"}},
            ]
        }

        job_id = self.app.put(url="/jobs", params=json.dumps(job), status=200).json[
            "job_id"
        ]

        self.assertIsNotNone(job_id)

        job = Session.query(Job).get(job_id)

        self.assertEqual(job.vo_name, "testvo")
        self.assertEqual(job.user_dn, self.TEST_USER_DN)
        self.assertEqual(job.source_se, "root://source.es")
        self.assertEqual("DELETE", job.job_state)
        self.assertIsNotNone(job.cred_id)

        dm = Session.query(DataManagement).filter(DataManagement.job_id == job_id).all()
        self.assertEqual(2, len(dm))

        self.assertEqual(dm[0].source_surl, "root://source.es/file")
        self.assertEqual(dm[1].source_surl, "root://source.es/file2")

        self.assertEqual(dm[1].file_metadata["a"], "b")

        self.assertEqual(dm[0].hashed_id, dm[1].hashed_id)

        for d in dm:
            self.assertEqual(d.vo_name, "testvo")
            self.assertEqual(d.file_state, "DELETE")
            self.assertEqual(d.source_se, "root://source.es")

        return str(job_id)

    @unittest.skip(
        "Deleting jobs in FTS are being decommissioned. Tests should be removed in the future."
    )
    def test_get_delete_job(self):
        """
        Submit a deletion job, get info via REST
        """
        job_id = self.test_simple_delete()

        job = self.app.get_json(url="/jobs/%s" % job_id, status=200).json
        files = self.app.get_json(url="/jobs/%s/dm" % job_id, status=200).json

        self.assertEqual(job["job_state"], "DELETE")
        self.assertEqual(files[0]["source_surl"], "root://source.es/file")
        self.assertEqual(files[1]["source_surl"], "root://source.es/file2")

    @unittest.skip(
        "Flask bug when static static_url_path='', OPTIONS always returns GET"
    )
    def test_cancel_delete(self):
        """
        Submit deletion job, then cancel
        """
        job_id = self.test_simple_delete()

        self.app.delete(url="/jobs/%s" % job_id, status=200)

        job = Session.query(Job).get(job_id)

        self.assertEqual("CANCELED", job.job_state)
        self.assertEqual(job.reason, "Job canceled by the user")
        self.assertIsNotNone(job.job_finished)

        dm = Session.query(DataManagement).filter(DataManagement.job_id == job_id).all()
        for d in dm:
            self.assertEqual("CANCELED", d.file_state)
            self.assertIsNotNone(d.finish_time)
            self.assertIsNotNone(d.job_finished)

    @unittest.skip(
        "Deleting jobs in FTS are being decommissioned. Tests should be removed in the future."
    )
    def test_delete_repeated(self):
        """
        Submit a deletion job with files repeated multiple times,
        they must land only once in the db
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "delete": [
                "root://source.es/file",
                {"surl": "root://source.es/file2", "metadata": {"a": "b"}},
                "root://source.es/file",
                "root://source.es/file2",
                "root://source.es/file3",
            ]
        }

        job_id = self.app.put(url="/jobs", params=json.dumps(job), status=200).json[
            "job_id"
        ]

        self.assertIsNotNone(job_id)

        dm = Session.query(DataManagement).filter(DataManagement.job_id == job_id).all()

        self.assertEqual(3, len(dm))
        registered = set()
        for f in dm:
            registered.add(f.source_surl)
        self.assertEqual(
            {
                "root://source.es/file",
                "root://source.es/file2",
                "root://source.es/file3",
            },
            registered,
        )

    @unittest.skip(
        "Deleting jobs in FTS are being decommissioned. Tests should be removed in the future."
    )
    def test_delete_file(self):
        """
        Submit a deletion job with a file:///
        Must be denied
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "delete": [
                "root://source.es/file",
                {"surl": "root://source.es/file2", "metadata": {"a": "b"}},
                "root://source.es/file",
                "root://source.es/file2",
                "file:///etc/passwd",
            ]
        }

        self.app.put(url="/jobs", params=json.dumps(job), status=400)
