from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3.model import Job


class TestJobModify(TestController):
    """
    Tests job modification
    """

    def test_job_priority(self):
        """
        Submit a job, change priority later
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": ["root://dest.ch/file"],
                }
            ],
            "params": {"priority": 2},
        }

        job_id = self.app.post_json(url="/jobs", params=job, status=200).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(2, job.priority)

        mod = {"params": {"priority": 4}}

        self.app.post_json(url="/jobs/%s" % str(job_id), params=mod, status=200)

        job = Session.query(Job).get(job_id)
        self.assertEqual(4, job.priority)

    def test_job_priority_invalid(self):
        """
        Submit a job, try to change priority to an invalid value later
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": ["root://dest.ch/file"],
                }
            ],
            "params": {"priority": 2},
        }

        job_id = self.app.post_json(url="/jobs", params=job, status=200).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(2, job.priority)

        mod = {"params": {"priority": "axxx"}}

        self.app.post_json(url="/jobs/%s" % str(job_id), params=mod, status=400)
