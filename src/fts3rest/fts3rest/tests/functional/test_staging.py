import json

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3.model import Job


class TestSubmitToStaging(TestController):
    """
    Tests for the job controller
    Focus in staging transfers
    """

    def test_submit_to_staging(self):
        """
        Submit a job into staging
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["srm://source.es/file"],
                    "destinations": ["srm://dest.ch/file"],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {
                "overwrite": True,
                "copy_pin_lifetime": 3600,
                "bring_online": 60,
                "verify_checksum": True,
            },
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        db_job = Session.query(Job).get(job_id)
        self.assertEqual(db_job.job_state, "STAGING")
        self.assertEqual(db_job.files[0].file_state, "STAGING")

        return job_id

    def test_submit_to_staging_no_lifetime(self):
        """
        Submit a job into staging, with pin lifetime not set
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["srm://source.es/file"],
                    "destinations": ["srm://dest.ch/file"],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "bring_online": 60, "verify_checksum": True},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        db_job = Session.query(Job).get(job_id)
        self.assertEqual(db_job.job_state, "STAGING")
        self.assertEqual(db_job.files[0].file_state, "STAGING")

        return job_id

    def test_multiple_bringonline(self):
        """
        Test a bring online job, with multiple files
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["srm://source.es/?SFN=/path/"],
                    "destinations": ["srm://dest.ch/file"],
                },
                {
                    "sources": ["srm://source.es/?SFN=/path/file2"],
                    "destinations": ["srm://dest.ch/file2"],
                },
                {
                    "sources": ["srm://source.es/?SFN=/path/file3"],
                    "destinations": ["srm://dest.ch/file3"],
                },
            ],
            "params": {
                "overwrite": True,
                "copy_pin_lifetime": 3600,
                "bring_online": 60,
                "verify_checksum": True,
            },
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        db_job = Session.query(Job).get(job_id)
        self.assertEqual(db_job.job_state, "STAGING")

        self.assertEqual(len(db_job.files), 3)

        # "Hashed" id must be equal so bulk bring online calls can be made
        # See https://its.cern.ch/jira/browse/FTS-145
        hid = db_job.files[0].hashed_id
        for f in db_job.files:
            self.assertEqual(f.file_state, "STAGING")
            self.assertEqual(f.hashed_id, hid)

    def test_submit_to_staging_no_bring_online(self):
        """
        Submit a job into staging, with bring_online not set
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["srm://source.es/file"],
                    "destinations": ["srm://dest.ch/file"],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {
                "overwrite": True,
                "copy_pin_lifetime": 60,
                "verify_checksum": True,
            },
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        db_job = Session.query(Job).get(job_id)
        self.assertEqual(db_job.job_state, "STAGING")
        self.assertEqual(db_job.files[0].file_state, "STAGING")

        return job_id
