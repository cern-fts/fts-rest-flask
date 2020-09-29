fts-rest migration to Flask and Python3
===
Carles Garcia Cabot
02/10/2020

---

Source: https://gitlab.cern.ch/fts/fts-rest-flask
JIRA Epic: https://its.cern.ch/jira/browse/FTS-1501

---

## About the migration
The migration of [fts-rest](https://gitlab.cern.ch:8443/fts/fts-rest) started after the decisions made in the [evaluation](https://its.cern.ch/jira/browse/FTS-1496).

---

The evaluation considered four Python 3 Web Frameworks for the migration:
- Django
- Flask
- Pyramid 
- FastAPI

---

Of those I reached the conclusion that Flask was the best option:
- Many users, active ecosystem. From Jetbrain's The State of Developer Ecosystem 2020:
 ![](https://codimd.web.cern.ch/uploads/upload_33952b0b8fb57e7c542567d11281814f.png)
- Its simplicity means that a significant amount of the current code can be reused. 
- We don't need any third-party plugins. For example, for authorization and authentication we can reuse our custom code. We don't need Flask-login. Pylon's Controllers will be converted to Flasks Blueprints, and the 'before' decorator will run the authorization code for each endpoint.
- The most important difference between Pylons and Flask is that Pylons uses Mako templates and Flask uses Jinja templates (HTML templates). Fortunately I was able to configure Mako's engine in Flask and so I didn't have to translate the templates.

## General points
- This is a migration, so the goal has been to copy the structure and code as much as possible to avoid breaking things, even if the quality of some parts could have been improved.

- We will support CentOS 7 Python 3.6 (good enough as .7 and .8 don't bring anything crucial. 3.6 EOL is end of 2021)

- I updated all Copyright issues that hadn't been updated. At some point I should added NOTICE, it's not necessary to have a notice in every file.

## History
You can see an approximate history of the development in the list of tickets in the JIRA Epic. Briefly:
- Evaluated options for migration
- Created the CI (initially static code analysis)
- Created a minimal Flask app to learn about the framework and do some proofs of concept
- Migrated DB models
- Migrated client
- Created build script for client
- Migrated exceptions
- Migrated routing
- Migrated controllers
- Migrated the test client + CI
- Migrated authentication and authorization
- Migrated functional tests
- Migrated admin config web pages 
- Created RPMs with Apache config + CI
- Configured SELinux
- Configured continuous delivery
- Deploy to fts-flask-03

## Development servers
- fts-flask-02: for development, server runs from virtual environment in /home with local DB. local user ftsflask
- fts-flask-03: pre-production environment, runs from RPM with DBOD ftsflask5. local user fts3

- You can already make successful tranfers with https://fts-flask-03.cern.ch:8446. I suggest you use the new client in the testing repository, you can install it with yum install fts-rest-client or alternatively install the wheel in a venv (you can get the wheel here (https://gitlab.cern.ch/fts/fts-rest-flask/-/jobs/10128577/artifacts/file/dist/fts_client_py3-1-py3-none-any.whl). The server contains fts-rest-server and fts-server connected to DBOD ftsflask5. The installation was done manually, as if done via puppet it fails when including the fts module, as it tries to install fts-rest (python2) and many other things.

- When I installed fts-server manually it failed because missing libzmq.so.5. I solved it by installing yum install zeromq-devel which is not a dependency currently

### Create a development server
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
### Create a development environment
- clone the repository and cd into it
- create a venv and activate it
- run `pip install --upgrade pip`
- run `pip install pip-tools`
- run `source pipcompile.sh`
- run `source pipsyncdev.sh`. If these steps fail, it's because you are missing some system dependencies. 
Check the beginning of .gitlab-ci/Dockerfile to see what you need to install.
- run `source precommit_install.sh`


### How to run development server
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

### Connect to local database
To access the config page:
```
INSERT INTO t_authz_dn VALUES ('yourdn');
```

### Run tests 
```
source runtests.sh
```
---

## DB
It only works with MySQL 5. MySQL 8 doesn't work because of the outdated version of SQLAlchemy in CentOS 7.

SQLAlchemy models: they are the same, some had to be updated to match the DB schema because they had been oudated for a long time. 
- We don't need Flask-SQLAlchemy: https://its.cern.ch/jira/browse/FTS-1538, https://its.cern.ch/jira/browse/FTS-1548

## Git workflow
- `Master` cannot be pushed to directly.
- Create a new branch for each ticket and merge it to master through a merge request.


## CI
I took the oportunity to start using Gitlab CI instead of Jenkins. With the new CI, we have static code analysis, functional testing, bulding and deployment.

To run the pipelines efficiently, I created Docker image containing git, python and the necessary tools for CI without having to install them in every run. Upload the image to the registry in the repository.

I created a prehook commit that everyone should install that does a subset of CI in order to catch errors early.

We now have test coverage which we didn't have before.

Run tests in CI with every Python version supported: in reality we only support the CentOS version, so Python3.6. However it's good to have that because the logs show things that will be removed in future versions, and things that may break. I considered Tox, but it didn't seem necessary and added complexity. Final solution: the docker image has all major python 3 version installed with pyenv. Before each stage in CI, the version is set accordingly.

Bandit runs in CI, some false positives, it should be checked regularly, it always fails.

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

## README
https://gitlab.cern.ch/fts/fts-rest-flask/-/blob/master/README.md

Already integrated in this document

## Miscellany
- ErrorasJson middleware converted to error handler
- Mako templates migrated by compiling them with the library

- See https://its.cern.ch/jira/browse/FTS-1536 for the migration of controllers.
- Migrated Pylon's webob exceptions to Flask's werkzeug exceptions
- As Controllers won't be used anymore, fts3rest.lib.base will be removed and replaced by fts3rest.model.meta, which contains Session

## Documentation
- https://its.cern.ch/jira/browse/FTS-1554 controllers/api.py: This contains code for the api documentation and is not trivial to migrate. Only some has been migrated in order to pass test_options.py. We'll need to find a way to migrate documentation. It should be written in the code and then converted to markdown or html with a tool. See also https://its.cern.ch/jira/browse/FTS-1618. The endpoints are documented with decorators that have not been migrated.


## Testing
- TestController. Tests migration, Flask test client wrapper
- Selenium tests are in a bad state, so no migrated: https://its.cern.ch/jira/browse/FTS-1613
- Same with unit tests: https://its.cern.ch/jira/browse/FTS-1614

Openid tests don't run in CI because the container would need a client registered and this is 
 difficult to set up. To run these tests in a development environment, the environment variables 'xdc_ClientId' and 'xdc_ClientSecret' must be set.


## Packaging and deployment
- We have a python package that can be build with setup.py (dist and bdist). It should be uploaded to PyPI.

- Some dependencies are not found in EPEL or any other community repositories so we have to package them and upload them to our repo. There's an easy way to generate an RPM from setup.py. I think these packages are listed in the spec.

- Spec file has been divided in client and server, plus subpackages don't exist anymore. Need to choose the package version number.

- Configured SELinux for the server. Wrote the rules in the RPM scriplets as writing a module is not well documented.

- Created a docker image, need to test it. Some users use containers such as Fermilab.

- Apache configuration: mod_wsgi for python3 is needed, and it cannot be found in the default repos in CC7
- Client already advertised to Cristina and DTO (it's beta)

### Python dependencies
This project uses [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies:
- `requirements.in`: list of dependencies for the production app
- `dev-requirements.in`: extra list of packages used for development (e.g. static code analysis)
- `pipcompile.sh`: run it in the development server in order to generate `requirements.txt`
- `pipsyncdev.sh`: run it afterwards to synchronize the virtual environment with the requirements.

### Installation requirements
Because we need mod_wsgi built for Python 3.6, we need to use rh-python36-mod_wsgi
```
yum-config-manager --enable centos-sclo-rh
yum install rh-python36-mod_wsgi
```
All other requirements are specified in the spec files.

### Build packages
Check .gitlab-ci.yml to see how the packages are built

## Probable causes if bugs appear:
- Python2 str is Python3 bytes
- Python2 filter/map return list, Python3 return generator

## Important changes
- In addition I renamed fts3config to ftsrestconfig. The problem is fts3 and ftsrest are too tightly coupled, and it's a problem.


## Problems
- One problem is that the development environment and the CI image run the code in a virtual environment with the latest dependencies, while the RPM uses outdated dependencies form the repositories.This means that some bug caused due to old dependencies won't be caught until production.
- Some new commits might have not been migrated to Python3
- Authentication for WebFTS doesn't work

## Todo:
- Check if client config file is read, or included in the rpm
- Relevant: https://its.cern.ch/jira/browse/FTS-1532
