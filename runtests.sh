#!/bin/bash

source venv/bin/activate
export PYTHONPATH=/home/ftsflask/fts-rest-flask/src:/home/ftsflask/fts-rest-flask/src/fts3rest
export FTS3TESTCONFIG=/home/ftsflask/fts-rest-flask/src/fts3rest/fts3rest/tests/fts3testconfig
python3 -m pytest -x src/fts3rest/fts3rest/tests/functional/test_job_submission.py
