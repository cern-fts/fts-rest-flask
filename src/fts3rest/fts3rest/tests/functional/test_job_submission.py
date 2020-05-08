import json
import socket
import time

from fts3rest.tests import TestController
from fts3rest.model.meta import Session
from fts3rest.model import Job
import random
from math import ceil


def _ceil_time():
    return ceil(time.time())


class TestJobSubmission(TestController):
    """
    Tests job submission
    """

    def _validate_submitted(self, job, no_vo=False, dn=TestController.TEST_USER_DN):
        self.assertNotEqual(job, None)
        files = job.files
        self.assertNotEqual(files, None)

        self.assertEqual(job.user_dn, dn)
        if no_vo:
            self.assertEqual(job.vo_name, "TestUser@cern.ch")
        else:
            self.assertEqual(job.vo_name, "testvo")
        self.assertEqual(job.job_state, "SUBMITTED")

        self.assertEqual(job.source_se, "root://source.es")
        self.assertEqual(job.dest_se, "root://dest.ch")
        self.assertEqual(job.overwrite_flag, True)
        self.assertEqual(job.verify_checksum, "b")
        self.assertEqual(job.job_type, "N")
        self.assertEqual(job.priority, 3)
        self.assertIsNone(job.max_time_in_queue)

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].file_state, "SUBMITTED")
        self.assertEqual(files[0].source_surl, "root://source.es/file")
        self.assertEqual(files[0].source_se, "root://source.es")
        self.assertEqual(files[0].dest_se, "root://dest.ch")
        self.assertEqual(files[0].file_index, 0)
        self.assertEqual(files[0].selection_strategy, "orderly")
        self.assertEqual(files[0].user_filesize, 1024)
        self.assertEqual(files[0].checksum, "adler32:1234")
        self.assertEqual(files[0].file_metadata["mykey"], "myvalue")
        if no_vo:
            self.assertEqual(files[0].vo_name, "TestUser@cern.ch")
        else:
            self.assertEqual(files[0].vo_name, "testvo")

        self.assertEqual(files[0].activity, "default")

        # Validate submitter
        self.assertEqual(socket.getfqdn(), job.submit_host)

    def test_submit(self):
        """
        Submit a valid job
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertTrue(job_id)  # not empty

        self._validate_submitted(Session.query(Job).get(job_id))

        return str(job_id)

    def test_submit_no_reuse(self):
        """
        Submit a valid job no reuse
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True, "reuse": False},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertTrue(job_id)

        self._validate_submitted(Session.query(Job).get(job_id))

        return str(job_id)

    def test_submit_no_reuse_N(self):
        """
        Submit a valid job, using 'N' instead of False
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True, "reuse": "N"},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertTrue(job_id)

        self._validate_submitted(Session.query(Job).get(job_id))

        return str(job_id)

    def test_submit_reuse(self):
        """
        Submit a valid reuse job
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True, "reuse": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertTrue(job_id)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.job_type, "Y")

        return job_id

    def test_submit_Y(self):
        """
        Submit a valid reuse job, using 'Y' instead of True
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": "Y", "verify_checksum": "Y", "reuse": "Y"},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertTrue(job_id)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.job_type, "Y")

    def test_submit_post(self):
        """
        Submit a valid job using POST instead of PUT
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        self._validate_submitted(Session.query(Job).get(job_id))

        return job_id

    def test_submit_with_port(self):
        """
        Submit a valid job where the port is explicit in the url.
        source_se and dest_se must exclude this port
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "srm://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["srm://source.es:8446/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        db_job = Session.query(Job).get(job_id)

        self.assertEqual(db_job.source_se, "srm://source.es")
        self.assertEqual(db_job.dest_se, "srm://dest.ch")

        self.assertEqual(db_job.files[0].source_se, "srm://source.es")
        self.assertEqual(db_job.files[0].dest_se, "srm://dest.ch")

        return job_id

    def test_submit_only_query(self):
        """
        Submit a valid job, without a path, but with a query in the url.
        This is valid for some protocols (i.e. srm)
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["srm://source.es/?SFN=/path/"],
                    "destinations": [dest_surl],
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

        job_id = self.app.put(
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
        self.assertEqual(db_job.copy_pin_lifetime, 3600)
        self.assertEqual(db_job.bring_online, 60)

        return job_id

    def test_null_checksum(self):
        """
        Valid job, with checksum explicitly set to null
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": None,
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].checksum, "ADLER32")

        return job_id

    def test_checksum_no_verify(self):
        """
        Valid job, with checksum, but verify_checksum is not set
        In the DB, it must end as 'r' (compatibility with FTS3 behaviour)
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "1234F",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].checksum, "1234F")
        self.assertEqual(job.verify_checksum, "t")

        return job_id

    def test_verify_checksum_target(self):
        """
        Valid job, verify checksum in destination.
        In the DB, it must end as 'r' (compatibility with FTS3 behaviour) or destination
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "1234F",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": "target"},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].checksum, "1234F")
        self.assertEqual(job.verify_checksum, "t")

        return job_id

    def test_verify_checksum_source(self):
        """
        Valid job, verify checksum in source.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "1234F",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": "source"},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].checksum, "1234F")
        self.assertEqual(job.verify_checksum, "s")

        return job_id

    def test_verify_checksum_both(self):
        """
        Valid job, verify checksum in source.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "1234F",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": "both"},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].checksum, "1234F")
        self.assertEqual(job.verify_checksum, "b")

        return job_id

    def test_verify_checksum_none(self):
        """
        Valid job, verify checksum none.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": "none"},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.verify_checksum, "n")

        return job_id

    def test_null_user_filesize(self):
        """
        Valid job, with filesize explicitly set to null
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "filesize": None,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was committed to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].user_filesize, 0)

        return job_id

    def test_no_vo(self):
        """
        Submit a valid job with no VO data in the credentials (could happen with plain SSL!)
        The job must be accepted, but assigned to the user's 'virtual' vo.
        """
        self.setup_gridsite_environment(no_vo=True)
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertGreater(len(job_id), 0)

        self._validate_submitted(Session.query(Job).get(job_id), no_vo=True)

    def test_no_vo_proxy(self):
        """
        Submit a valid job with no VO data in the credentials, but still being a proxy.
        The job must be accepted, but assigned to the user's 'virtual' vo.
        """
        proxy_dn = self.TEST_USER_DN + "/CN=proxy"
        self.setup_gridsite_environment(no_vo=True, dn=proxy_dn)
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertGreater(len(job_id), 0)

        self._validate_submitted(
            Session.query(Job).get(job_id), no_vo=True, dn=proxy_dn
        )

    def test_retry(self):
        """
        Submit with a specific retry value
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {
                "overwrite": True,
                "verify_checksum": True,
                "retry": 42,
                "retry_delay": 123,
            },
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self._validate_submitted(job)
        self.assertEqual(job.retry, 42)
        self.assertEqual(job.retry_delay, 123)

    def test_with_activity(self):
        """
        Submit a job specifiying activities for the files
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file"],
                    "destinations": [dest_surl],
                    "activity": "my-activity",
                },
                {
                    "sources": ["https://source.es/file2"],
                    "destinations": ["https://dest.ch/file2"],
                    "activity": "my-second-activity",
                },
            ]
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # Make sure it was commited to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.files[0].activity, "my-activity")
        self.assertEqual(job.files[1].activity, "my-second-activity")

    def test_surl_with_spaces(self):
        """
        Submit a job where the surl has spaces at the beginning and at the end
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["root://source.es/file\n \r "],
                    "destinations": ["\r\n" + dest_surl + "\n\n \n"],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024.0,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.put(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]
        # Make sure it was commited to the DB
        self.assertGreater(len(job_id), 0)

        job = Session.query(Job).get(job_id)
        self._validate_submitted(job)

    def test_submit_different_protocols(self):
        """
        Source and destination protocol mismatch
        For REST <= 3.2.3, this used to be forbidden, but it was decided to allow it
        https://its.cern.ch/jira/browse/FTS-97
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(1, len(job.files))
        self.assertEqual("http://source.es:8446/file", job.files[0].source_surl)
        self.assertEqual(dest_surl, job.files[0].dest_surl)

    def test_submit_with_cloud_cred(self):
        """
        Submit a job specifying cloud credentials
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["dropbox://dropbox.com/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {"overwrite": True, "verify_checksum": True},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(1, len(job.files))
        self.assertEqual("dropbox://dropbox.com/file", job.files[0].source_surl)
        self.assertEqual(dest_surl, job.files[0].dest_surl)

    def test_submit_protocol_params(self):
        """
        Submit a transfer specifying some protocol parameters
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                    "selection_strategy": "orderly",
                    "checksum": "adler32:1234",
                    "filesize": 1024,
                    "metadata": {"mykey": "myvalue"},
                }
            ],
            "params": {
                "overwrite": True,
                "verify_checksum": True,
                "timeout": 1234,
                "nostreams": 42,
                "buffer_size": 1025,
                "strict_copy": True,
            },
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertTrue(job.internal_job_params is not None)
        params = job.internal_job_params.split(",")
        self.assertIn("timeout:1234", params)
        self.assertIn("nostreams:42", params)
        self.assertIn("buffersize:1025", params)
        self.assertIn("strict", params)

    def test_submit_with_priority(self):
        """
        Submit a job specifying the priority
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                }
            ],
            "params": {"priority": 5,},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertEqual(job.priority, 5)

    def test_submit_max_time_in_queue(self):
        """
        Submits a job specifying the maximum time it should stay in the queue.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                }
            ],
            "params": {"max_time_in_queue": 8},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        # See FTS-311
        # max_time_in_queue was effectively ignored by FTS3
        # Since FTS-311, this field stores the timestamp when the job expires
        job = Session.query(Job).get(job_id)
        self.assertGreater(job.max_time_in_queue, _ceil_time())
        self.assertLessEqual(job.max_time_in_queue, (8 * 60 * 60) + _ceil_time())

    def test_submit_max_time_in_queue_suffix(self):
        """
        Submits a job specifying the maximum time it should stay in the queue.
        Use a suffix.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest.ch:8447/file" + str(random.randint(0, 100))
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                }
            ],
            "params": {"max_time_in_queue": "4s"},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertGreater(job.max_time_in_queue, _ceil_time())
        self.assertLessEqual(job.max_time_in_queue, 8 + _ceil_time())

    def test_submit_max_time_in_queue_suffix2(self):
        """
        Submits a job specifying the maximum time it should stay in the queue.
        Use a suffix.
        """
        self.setup_gridsite_environment()
        self.push_delegation()
        dest_surl = "root://dest" + str(random.randint(0, 100)) + ".ch:8447/file"
        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": [dest_surl],
                }
            ],
            "params": {"max_time_in_queue": "2m"},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        job = Session.query(Job).get(job_id)
        self.assertGreater(job.max_time_in_queue, _ceil_time())
        self.assertLessEqual(job.max_time_in_queue, 120 + _ceil_time())

    def test_submit_ipv4(self):
        """
        Submit a job with IPv4 only
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": ["root://destipv4.ch:8447/file"],
                }
            ],
            "params": {"ipv4": True},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        jobdb = Session.query(Job).get(job_id)
        self.assertIn("ipv4", jobdb.internal_job_params)
        self.assertNotIn("ipv6", jobdb.internal_job_params)

        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": ["root://destipv4tofalse.ch:8447/file"],
                }
            ],
            "params": {"ipv4": False},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        jobdb = Session.query(Job).get(job_id)
        self.assertTrue(
            jobdb.internal_job_params is None or "ipv4" not in jobdb.internal_job_params
        )
        self.assertTrue(
            jobdb.internal_job_params is None or "ipv6" not in jobdb.internal_job_params
        )

    def test_submit_ipv6(self):
        """
        Submit a job with IPv6 only
        """
        self.setup_gridsite_environment()
        self.push_delegation()

        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": ["root://destipv6.ch:8447/file"],
                }
            ],
            "params": {"ipv6": True},
        }
        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        jobdb = Session.query(Job).get(job_id)
        self.assertIn("ipv6", jobdb.internal_job_params)
        self.assertNotIn("ipv4", jobdb.internal_job_params)

        job = {
            "files": [
                {
                    "sources": ["http://source.es:8446/file"],
                    "destinations": ["root://destipv6tofalse.ch:8447/file"],
                }
            ],
            "params": {"ipv6": False},
        }

        job_id = self.app.post(
            url="/jobs",
            content_type="application/json",
            params=json.dumps(job),
            status=200,
        ).json["job_id"]

        jobdb = Session.query(Job).get(job_id)
        self.assertTrue(
            jobdb.internal_job_params is None or "ipv4" not in jobdb.internal_job_params
        )
        self.assertTrue(
            jobdb.internal_job_params is None or "ipv6" not in jobdb.internal_job_params
        )
