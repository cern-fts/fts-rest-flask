import json
import random

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import Job


class TestJobSubmissionMetadata(TestController):
    """
    Tests job submission with metadata
    """

    def test_job_metadata_string(self):
        """
        Submit a job specifying job metadata as string
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                }
            ],
            "params": {
                "job_metadata": "This is my job metadata",
            },
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(
            job.job_metadata,
            {"label": "This is my job metadata", "auth_method": "certificate"},
        )

    def test_file_metadata_string(self):
        """
        Submit a job specifying file metadata as string
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "metadata": "This is my file metadata",
                }
            ],
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(
            job.files[0].file_metadata, {"label": "This is my file metadata"}
        )
