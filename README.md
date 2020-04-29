# About the migration
The migration of [fts-rest](https://gitlab.cern.ch:8443/fts/fts-rest) has started after the decisions made in 
the [evaluation](https://its.cern.ch/jira/browse/FTS-1496).

The development is happening at fts-flask.cern.ch, with the local user ftsflask 

# Git workflow
- `Master` cannot be pushed to directly.
- Create a new branch for each ticket and merge it to master.

# Gitlab CI
The current pipeline runs for every push in every branch:
- black: fails if the code hasn't been formatted with black
- pylint: fails if the code has syntax errors. If you are sure that pylint is mistaken, add `# pylint: skip-file` at
 the beginning of the relevant file.
- radon: fails if the code complexity is too high
- bandit: detects potential security issues in the code, but it's allowed to fail as there may be false positives
Merge requests will proceed only if the pipeline succeeds.
In case of emergency the pipeline can be [skipped](https://docs.gitlab.com/ee/ci/yaml/#skipping-jobs).

The pipeline runs in a container from the image tagged as `ci`. The dockerfile is in the .gitlab-ci directory and the image is in the container registry for this project. The image contains the Python tools preinstalled so the CI runs faster.

Developers should add the `pre-commit` hook to their local repository. This scripts does this for every commit:
- Runs black to format the changed files.
- Runs pylint only on the changed files for speed. As pylint works better when it is run on all the project, some rules have been disabled.
- Runs radon and bandit only on the changed files.
The hook can be skipped, in case bandit detects false positives, with the commit option `--no-verify`.

# Python dependencies
This project uses [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies:
- `requirements.in`: list of dependencies for the production app
- `dev-requirements.in`: extra list of packages used for development (e.g. static code analysis)
- `pipcompile.sh`: run it in the development server in order to generate `requirements.txt`
- `pipsyncdev.sh`: run it afterwards to synchronize the virtual environment with the requirements.

# Installation requirements
Because we need mod_wsgi built for Python 3.6, we need to use httpd24-httpd
- yum install python3-devel openssl-devel swig gcc gcc-c++ make httpd-devel mysql-devel
- gfal2-python3
- yum-config-manager --enable centos-sclo-rh
- yum install rh-python36-mod_wsgi
# Installation requirements for development
To create a development venv: use --system-packages in order to use gfal2-python3

# How to run development server
Flask:
```
export PYTHONPATH=/home/ftsflask/fts-rest-flask/src:/home/ftsflask/fts-rest-flask/src/fts3rest 
export FLASK_APP=/home/ftsflask/fts-rest-flask/src/fts3rest/fts3restwsgi.py
export FLASK_ENV=development
flask run 
curl  http://127.0.0.1:5000/hello
```
httpd24:
```
cp /home/ftsflask/fts-rest-flask/src/fts3rest/httpd_fts.conf /etc/httpd/conf.d/
systemctl start httpd
curl http://localhost:80/hello
```

# Connect to local database
To access the config page:
```
INSERT INTO t_authz_dn VALUES ('yourdn');

```

# Run tests 
```
source venv/bin/activate
export PYTHONPATH=/home/ftsflask/fts-rest-flask/src:/home/ftsflask/fts-rest-flask/src/fts3rest 
export FTS3TESTCONFIG=/home/ftsflask/fts-rest-flask/src/fts3rest/fts3rest/tests/fts3testconfig
python3 -m pytest -x src/fts3rest/fts3rest/tests/functional/test_job_submission.py 
```
# Migration status
Starting with the client, as it requires small changes only. Will not migrate pycurlrequest.py, as it is not used
 anymore. 