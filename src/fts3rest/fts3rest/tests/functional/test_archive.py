from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.lib.middleware.fts3auth.credentials import UserCredentials
from fts3.model import ArchivedJob, ArchivedFile


class TestArchive(TestController):
    """
    Archived jobs
    """

    def _insert_job(self):
        job = ArchivedJob()

        job.job_id = "111-222-333"
        job.job_state = "CANCELED"
        job.user_dn = TestController.TEST_USER_DN

        archived = ArchivedFile()
        archived.job_id = job.job_id
        archived.file_id = 1234
        archived.file_state = "CANCELED"
        archived.source_se = "srm://source"
        archived.dest_se = "srm://dest"

        Session.merge(job)
        Session.merge(archived)
        Session.commit()
        return job.job_id

    def test_get_archive_index(self):
        """
        Ask for the index
        """
        self.setup_gridsite_environment()
        self.app.get(url="/archive/", status=200)

    def test_get_from_archive(self):
        """
        Query an archived job must succeed
        """
        self.setup_gridsite_environment()

        job_id = self._insert_job()
        job = self.app.get(url="/archive/%s" % job_id, status=200).json

        self.assertEqual(job["job_id"], job_id)
        self.assertEqual(job["job_state"], "CANCELED")

        self.assertEqual(len(job["files"]), 1)

        self.assertEqual(job["files"][0]["file_state"], "CANCELED")
        self.assertEqual(job["files"][0]["source_se"], "srm://source")
        self.assertEqual(job["files"][0]["dest_se"], "srm://dest")
        self.assertEqual(job["files"][0]["file_id"], 1234)

    def test_get_field_from_archive(self):
        """
        Query a specific field from an archived job
        """
        self.setup_gridsite_environment()

        job_id = self._insert_job()
        state = self.app.get(url="/archive/%s/job_state" % job_id, status=200).json
        self.assertEqual(state, "CANCELED")

    def test_missing_job(self):
        """
        Query a job id that does not exist
        """
        self.setup_gridsite_environment()
        error = self.app.get(url="/archive/1234-5678-98765", status=404).json
        self.assertEqual(error["status"], "404 Not Found")

    def test_get_job_forbidden(self):
        """
        Ask for a job we don't have permission to get
        """
        self.setup_gridsite_environment()
        job_id = self._insert_job()

        # Trick to force a 'denied'
        old_granted = UserCredentials.get_granted_level_for
        UserCredentials.get_granted_level_for = lambda self_, op: None

        error = self.app.get("/archive/%s" % job_id, status=403).json

        UserCredentials.get_granted_level_for = old_granted

        self.assertEqual(error["status"], "403 Forbidden")

    def test_get_missing_field(self):
        """
        Ask for a field that doesn't exist
        """
        self.setup_gridsite_environment()
        job_id = self._insert_job()

        error = self.app.get(
            url="/archive/%s/not_really_a_field" % job_id, status=404
        ).json

        self.assertEqual(error["status"], "404 Not Found")
        self.assertEqual(error["message"], "No such field")
