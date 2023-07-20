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

    def test_job_metadata_JSON(self):
        """
        Submit a job specifying job metadata as JSON
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
                "job_metadata": {"key": "This is my test job metadata"},
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
            {"key": "This is my test job metadata", "auth_method": "certificate"},
        )

    def test_file_metadata_string_multiple(self):
        """
        Submit a job with multiple entries specifying file metadata as string
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file1"],
                    "destinations": [dest_surl],
                    "metadata": "This is my file metadata",
                },
                {
                    "sources": ["https://source.ch:8446/file2"],
                    "destinations": [dest_surl],
                    "metadata": "This is my file metadata",
                },
                {
                    "sources": ["https://source.ch:8446/file3"],
                    "destinations": [dest_surl],
                    "metadata": "This is my file metadata",
                },
                {
                    "sources": ["https://source.ch:8446/file4"],
                    "destinations": [dest_surl],
                    "metadata": "This is my file metadata",
                },
            ],
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)

        for file in job["files"]:
            self.assertEqual(file.file_metadata, {"label": "This is my file metadata"})

    def test_file_metadata_JSON(self):
        """
        Submit a job specifying file metadata as JSON
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "metadata": {"key": "This is my file metadata"},
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
            job.files[0].file_metadata, {"key": "This is my file metadata"}
        )

    def test_staging_metadata_string(self):
        """
        Submit a job specifying staging metadata as string
        note: job submission expected to fail
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "staging_metadata": "This is my test staging metadata",
                }
            ],
        }
        message = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=400,
        ).json["message"]
        self.assertIn("not in JSON format", message)

    def test_staging_metadata_JSON(self):
        """
        Submit a Job specifying staging metadata as JSON
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "staging_metadata": {"key": "This is my test staging metadata"},
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
            job.files[0].staging_metadata, {"key": "This is my test staging metadata"}
        )

    def test_archive_metadata_string(self):
        """
        Submit a Job specifying archive metadata as string
        note: job submission expected to fail
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "archive_metadata": "This is my test archive metadata",
                }
            ],
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=400,
        )  # No Job Id Returned

    def test_archive_metadata_JSON(self):
        """
        Submit a Job specifying archive metadata as JSON
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "archive_metadata": {"key": "This is my test archive metadata"},
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
            job.files[0].archive_metadata, {"key": "This is my test archive metadata"}
        )

    def test_staging_metadata_JSON_exceeding_size(self):
        """
        Submit a Job specifying staging metadata as JSON > 1024 bytes
        note: job submission expected to fail
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "staging_metadata": {
                        "key": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Scelerisque varius morbi enim nunc faucibus a pellentesque sit. Amet purus gravida quis blandit turpis. Ut tristique et egestas quis ipsum. Nisi vitae suscipit tellus mauris a diam. Placerat orci nulla pellentesque dignissim enim sit amet venenatis. Id leo in vitae turpis. Dictum at tempor commodo ullamcorper a lacus vestibulum. Auctor eu augue ut lectus arcu bibendum. Arcu cursus vitae congue mauris rhoncus aenean. Gravida neque convallis a cras. Id porta nibh venenatis cras sed felis. Natoque penatibus et magnis dis parturient montes nascetur ridiculus. In fermentum et sollicitudin ac. Eu sem integer vitae justo eget magna fermentum iaculis. Orci sagittis eu volutpat odio facilisis mauris. Sit amet porttitor eget dolor morbi non arcu risus. Eu mi bibendum neque egestas congue quisque egestas diam in. Aliquet nibh praesent tristique magna sit amet purus. Egestas diam in arcu cursus euismod quis. Ipsum dolor sit amet consectetur. Cursus metus aliquam eleifend mi in nulla posuere. Pellentesque dignissim enim sit amet venenatis urna cursus eget nunc"
                    },
                }
            ],
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=400,
        )

    def test_archive_metadata_JSON_exceeding_size(self):
        """
        Submit a Job specifying archive metadata as JSON > 1024 bytes
        note: job submission expected to fail
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "https://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["https://source.ch:8446/file"],
                    "destinations": [dest_surl],
                    "archive_metadata": {
                        "key": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Scelerisque varius morbi enim nunc faucibus a pellentesque sit. Amet purus gravida quis blandit turpis. Ut tristique et egestas quis ipsum. Nisi vitae suscipit tellus mauris a diam. Placerat orci nulla pellentesque dignissim enim sit amet venenatis. Id leo in vitae turpis. Dictum at tempor commodo ullamcorper a lacus vestibulum. Auctor eu augue ut lectus arcu bibendum. Arcu cursus vitae congue mauris rhoncus aenean. Gravida neque convallis a cras. Id porta nibh venenatis cras sed felis. Natoque penatibus et magnis dis parturient montes nascetur ridiculus. In fermentum et sollicitudin ac. Eu sem integer vitae justo eget magna fermentum iaculis. Orci sagittis eu volutpat odio facilisis mauris. Sit amet porttitor eget dolor morbi non arcu risus. Eu mi bibendum neque egestas congue quisque egestas diam in. Aliquet nibh praesent tristique magna sit amet purus. Egestas diam in arcu cursus euismod quis. Ipsum dolor sit amet consectetur. Cursus metus aliquam eleifend mi in nulla posuere. Pellentesque dignissim enim sit amet venenatis urna cursus eget nunc"
                    },
                }
            ],
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=400,
        )
