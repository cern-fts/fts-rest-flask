# About the migration
The migration of [fts-rest](https://gitlab.cern.ch:8443/fts/fts-rest) started after the decisions made in 
the [evaluation](https://its.cern.ch/jira/browse/FTS-1496).

The development is happening at fts-flask.cern.ch, with the local user ftsflask 

# Git workflow
- `Master` cannot be pushed to directly.
- Create a new branch for each ticket and merge it to master through a merge request.

# Gitlab CI
The current pipeline runs for every push in every branch:
- black: fails if the code hasn't been formatted with black
- pylint: fails if the code has syntax errors. If you are sure that pylint is mistaken, add `# pylint: skip-file` at
 the beginning of the relevant file. Runs for every supported Python3 version
- radon: fails if the code complexity is too high
- functional tests: Run for every supported Python3 version
- bandit: detects potential security issues in the code, but it's allowed to fail as there may be false positives.
To ignore a false positive, append `# nosec"` to the offending line
- build: RPM for the client and server, plus sdist and wheel for the client
- deploy: upload client and server RPM to the FTS testing repository

Merge requests will proceed only if the pipeline succeeds.

In case of emergency the pipeline can be [skipped](https://docs.gitlab.com/ee/ci/yaml/#skipping-jobs).

The pipeline runs in a container from the image tagged as `ci`. The dockerfile is in the .gitlab-ci directory and the 
image is in the container registry for this project. The image contains the Python tools preinstalled so the CI runs faster.
To build and push the image, cd to .gitlab-ci and run .docker_push.sh. This should be done when new dependencies are added.

Developers should add the `pre-commit` hook to their local repository. This scripts does this for every commit:
- Runs black to format the changed files.
- Runs pylint only on the changed files for speed. As pylint works better when it is run on all the project, some rules have been disabled.
- Runs radon and bandit only on the changed files.
The hook can be skipped, in case bandit detects false positives, with the commit option `--no-verify`.

# Functional tests
Openid tests don't run in CI because the container would need a client registered and this is 
 difficult to set up. To run these tests in a development environment, the environment variables 'xdc_ClientId' and 'xdc_ClientSecret' must be set.

# Python dependencies
This project uses [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies:
- `requirements.in`: list of dependencies for the production app
- `dev-requirements.in`: extra list of packages used for development (e.g. static code analysis)
- `pipcompile.sh`: run it in the development server in order to generate `requirements.txt`
- `pipsyncdev.sh`: run it afterwards to synchronize the virtual environment with the requirements.

# Installation requirements
Because we need mod_wsgi built for Python 3.6, we need to use rh-python36-mod_wsgi
```
yum-config-manager --enable centos-sclo-rh
yum install rh-python36-mod_wsgi
```
All other requirements are specified in the spec files.

# Build packages
Check .gitlab-ci.yml to see how the packages are built


# Create a development server
```bash
# Create VM
ssh garciacc@aiadm.cern.ch
unset OS_PROJECT_ID;
unset OS_TENANT_ID;
unset OS_TENANT_NAME;
export OS_PROJECT_NAME="IT FTS development";
ai-bs --foreman-hostgroup fts/flask --cc7 --foreman-environment ftsclean \
      --landb-responsible fts-devel --nova-flavor m2.large \
      fts-flask-02
           
# Install dependencies
ssh root@fts-flask-02
yum install centos-release-scl-rh
yum-config-manager --enable centos-sclo-rh
yum install python3-devel openssl-devel swig gcc gcc-c++ make httpd-devel \
mysql-devel gfal2-python3 gfal2-plugin-mock rh-python36-mod_wsgi \
git mariadb mariadb-server gridsite -y

# Prepare DB and log directories
systemctl start mariadb    
mkdir /var/run/mariadb             
chown mysql:mysql  /var/run/mariadb
mkdir /var/log/fts3rest
chown ftsflask /var/log/fts3rest

# Prepare application and Python dependencies
su ftsflask
cd
git clone https://gitlab.cern.ch/fts/fts-rest-flask.git
cd fts-rest-flask                 
# use --system-site-packages in order to use gfal2-python3      
python3 -m venv venv --system--site-packages
source venv/bin/activate
pip install --upgrade pip
pip install pip-tools
. ./pipcompile.sh 
. ./pipsyncdev.sh
                                            
# Load DB
cd ..
curl -O https://gitlab.cern.ch/fts/fts3/-/raw/fts-oidc-integration/src/db/schema/mysql/fts-schema-6.0.0.sql
mysql_secure_installation # put a password for root
echo "CREATE DATABASE ftsflask;" | mysql --user=root --password
mysql --user=root --password ftsflask < fts-schema-6.0.0.sql
echo "CREATE USER ftsflask;" | mysql --user=root --password
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'ftsflask'@'localhost' IDENTIFIED BY 'anotherpassword';" | mysql --user=root --password
cd fts-rest-flask
. runtests.sh

# Prepare server
exit
cp fts-rest-flask/src/fts3rest/httpd_fts.conf /etc/httpd/conf.d/
setenforce 0
chmod o+rx -R /home/ftsflask/
systemctl restart httpd


```

# Create a development environment
- clone the repository and cd into it
- create a venv and activate it
- run `pip install --upgrade pip`
- run `pip install pip-tools`
- run `source pipcompile.sh`
- run `source pipsyncdev.sh`. If these steps fail, it's because you are missing some system dependencies. 
Check the beginning of .gitlab-ci/Dockerfile to see what you need to install.
- run `source precommit_install.sh`


# How to run development server
Flask:
```
export PYTHONPATH=/home/ftsflask/fts-rest-flask/src:/home/ftsflask/fts-rest-flask/src/fts3rest 
export FLASK_APP=/home/ftsflask/fts-rest-flask/src/fts3rest/fts3restwsgi.py
export FLASK_ENV=development
flask run 
curl  http://127.0.0.1:5000/hello
```
httpd:
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
source runtests.sh
```
