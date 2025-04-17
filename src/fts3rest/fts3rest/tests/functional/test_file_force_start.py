import json
import random

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import Job


class TestFileForceStart(TestController):
    """
    Test transfer force start mechanism
    """

    def test_file_force_start(self):
        """
        Submit a valid job then trigger force start (as administrator).
        Should succeed
        """
        self.setup_gridsite_environment(ftsadmin=True)
        self.push_delegation()
        job = {
            "files": [
                {
                    "sources": ["https://source.ch/file"],
                    "destinations": [
                        "https://destination.ch/file" + str(random.randint(0, 100))
                    ],
                }
            ],
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        self.assertTrue(job_id)

        files = Session.query(Job).get(job_id).files
        self.assertEqual(1, len(files))
        self.assertEqual(files[0].file_state, "SUBMITTED")

        # Save "file_id" before running future queries
        # (SQLAlchemy would expire the "files" object)
        file_id = files[0].file_id

        result = self.app.post(
            url="/admin/force-start",
            content_type="application/json",
            params=f"[{file_id}]",
            status=200,
        ).json

        self.assertEqual(1, len(result))
        self.assertEqual(file_id, result[0]["file_id"])
        self.assertTrue("FORCE_START" in result[0]["message"])

    def test_file_force_start_not_submitted(self):
        """
        Submit a valid job then trigger force start on a file outside "SUBMITTED" state (as administrator).
        Should succeed, but return response will have an error
        """
        self.setup_gridsite_environment(ftsadmin=True)
        self.push_delegation()
        job = {
            "files": [
                {
                    "sources": ["https://source.ch/file"],
                    "destinations": [
                        "https://destination.ch/file" + str(random.randint(0, 100))
                    ],
                }
            ],
            "params": {
                "bring_online": 86400,
            },
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        self.assertTrue(job_id)

        files = Session.query(Job).get(job_id).files
        self.assertEqual(1, len(files))
        self.assertEqual(files[0].file_state, "STAGING")

        # Save "file_id" before running future queries
        # (SQLAlchemy would expire the "files" object)
        file_id = files[0].file_id

        result = self.app.post(
            url="/admin/force-start",
            content_type="application/json",
            params=f"[{file_id}]",
            status=200,
        ).json

        self.assertEqual(1, len(result))
        self.assertEqual(file_id, result[0]["file_id"])
        self.assertTrue(all(s in result[0]["error"] for s in ["not", "SUBMITTED"]))

    def test_file_force_start_unauthorized(self):
        """
        Submit a valid job then trigger force start (not administrator).
        Should not be allowed
        """
        self.setup_gridsite_environment(ftsadmin=False)
        self.push_delegation()
        job = {
            "files": [
                {
                    "sources": ["https://source.ch/file"],
                    "destinations": [
                        "https://destination.ch/file" + str(random.randint(0, 100))
                    ],
                }
            ],
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        self.assertTrue(job_id)

        files = Session.query(Job).get(job_id).files
        self.assertEqual(1, len(files))
        self.assertEqual(files[0].file_state, "SUBMITTED")

        self.app.post(
            url="/admin/force-start",
            content_type="application/json",
            params=f"[{files[0].file_id}]",
            status=403,
        )
