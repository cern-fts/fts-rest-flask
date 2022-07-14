FTS3-REST-Flask
===============

FTS3-REST-Flask is the RESTful API for the FTS3 Service.  

This is the front-facing component to communicate with the FTS3 Service,
allowing submission of transfers, querying transfer updates, as well as configuration management.  

The project consists of an Apache module running Python3 + Flask. 
It is also a direct continuation of the former [fts-rest][1], where the migration 
decision and evaluation can be seen [here][2].

## Installation

The project should be installed via RPMs, provided via the FTS repository.

### Installing the client

Make sure to have the FTS repositories enabled:
- [production][3] repository: official RPMs deemed ready for production
- [development][4] repository: RPMs built on the latest `develop` branch commit

#### Installing the client:
```shell
$ yum install -y fts-rest-client
```

#### Installing the server

The project needs `mod_wsgi` built for Python 3.6, which on Centos 7 is provided by the `rh-python36-mod_wsgi` package.
All other requirements are specified in the spec files.
```shell
$ yum-config-manager --enable centos-sclo-rh
$ yum install -y rh-python36-mod_wsgi
$ yum install -y fts-rest-server
```

Configuring the server is done via the following two configuration files:
- `/etc/fts3/fts3restconfig`
- `/etc/htpd/conf.d/fts3rest.conf`

## Development

The project is tracked using JIRA, under the [FTS Project][5] (requires CERN log-in). 
Soon the project will be mirrored on GitHub, where issues and pull requests are also accepted (and encouraged!). 

For development purposes, using a virtual environment is encouraged.

### Git Workflow

This project follows a simplified [GitFlow][6] model. The main branch is the `develop` branch,
with `master` being reserved only for tagged released.

Feature branches are developed separately and merged into the `develop` branch.
When preparing a release, either `develop` is merged directly into `master`
or a release branch is created. Production hotfixes are allowed only in case of necessity.
Both release and hotfix branch changes must be merged back into `develop`.

### Development workflow

When taking on a task, the following workflow model should be followed:
1. Create a JIRA ticket for the identified problem
2. Estimate the magnitude of the task:
    - Small changes can go directly on the `develop` branch
    - Larger changes must go into a separate feature branch
3. Implement and test your changes
4. Merge them into the `develop` branch:
    - Merge large changes via merge requests and request code review
    - Changes affecting the database must also be code reviewed!
5. Close the JIRA ticket and mark the appropriate `fixVersion`

### Continuous Integration

The project uses Gitlab-CI for CI/CD. The [pipeline][7] runs for every push, in every branch:
- black: checks code must be formatted with `black`
- pylint: checks for syntax errors (runs for every supported Python3 version)
  - If you are sure that pylint is mistaken, add `# pylint: skip-file` at the beginning of the relevant file
- functional tests: run for every supported Python3 version
- bandit: detects potential security issues in the code
  - Allowed to fail as it flags many false positives.
  - To ignore a false positive, append `# nosec` to the offending line
- build: RPM for the client and server, plus `sdist` and `wheel` for the client
- deploy: upload client and server RPM to the FTS testing repository

Merge requests will proceed only if the pipeline succeeds.  
In case of emergency the pipeline can be [skipped][8].

The pipeline runs in a container from the image tagged as `ci`. The dockerfile is in the `.gitlab-ci` directory and the 
image is hosted in the container registry of this project. The image contains the pre-installed Python environment 
in order to speed up CI execution. When new environment is desired (such as new or upgraded dependencies), 
a new image must be created via the `.gitlab-ci/docker/docker_push.sh` script.

#### During development

Developers may add the `.gitlab-ci/pre-commit` hook to their local repository, 
enabling the following checks before every commit:
- Run `black` to format the changed files
- Run `pylint` only on the changed files
  - Note: As pylint works better when it is run on the full project, some rules have been disabled
- Run `radon` and `bandit` only on the changed files
  - In case of false positives, the hook can be skipped with the commit option `--no-verify`

A convenience script is provided to install the `pre-commit` hook:
```shell
$ cd .gitlab-ci/
$ ./precommit_install.sh
```

### Python dependencies

The project uses [pip-tools][9] to manage dependencies:
- `requirements.in`: list of dependencies for the production app
- `dev-requirements.in`: extra list of packages used for development (e.g. static code analysis)

### Setting up the development environment

The `pipcompile.sh` script is provided to help set up a development environment:
```shell
$ virtualenv venv
$ source venv/bin/activate
(venv) $ pip install --upgrade pip
(venv) $ pip install pip-tools
(venv) $ ./pipcompile.sh --sync
```

Running `pipcompile.sh` will generate `requirements.txt`. Running the command with `--sync`
will also synchronize the virtual environment with the requirements.

Additionally, you will need to configure the HTTPd config file. 
A template version for development is offered at `src/fts3rest/fts3rest_dev_conf.in`. 
To fill it with the right paths and install it, run the `install-httpd-dev.sh` script:
```shell
$ cd src/fts3rest/
$ ./install-httpd-dev.sh
```

### Functional tests

The functional tests reside under `src/fts3rest/fts3rest/tests/functional`. 

In oder to run the tests, a fully functional MySQL-compatible database is required.
The database must have the appropriate FTS schema and the connection details configured 
in the FTS3 REST config file. 

Example on Centos 7 with locally installed `mariadb`: 
```shell
$ wget https://gitlab.cern.ch/fts/fts3/-/raw/v3.11.0/src/db/schema/mysql/fts-schema-7.0.0.sql
$ mysql -u root --execute "CREATE DATABASE ftsflask;"
$ mysql -u root --execute "CREATE USER 'fts3'@'%';"
$ mysql -u root --execute "GRANT ALL PRIVILEGES ON ftsflask.* TO 'fts3'@'%' IDENTIFIED BY 'ftsflaskpass';"
$ mysql -u fts3 --password=ftsflaskpass ftsflask
MariaDB [ftsflask]> source fts-schema-7.0.0.sql
```

Before running the tests, make sure to include the `fts3rest` project in the `PYTHONPATH`.  
Additionally, the `FTS3TESTCONFIG` environment variable can also be set to use a different config file during testing:
```shell
$ export PYTHONPATH="${PROJECT_DIR}/src:${PROJECT_DIR}/src/fts3rest"
$ export FTS3TESTCONFIG="${PROJECT_DIR}/src/fts3rest/fts3rest/tests/fts3testconfig"
```

For ease-of-use, the `runtests.sh` script is provided:
```shell
$ cd src/fts3rest
$ ./runtests.sh
```

**Note**: OIDC tests are not run in the CI as the container would need a client registered and this has not yet been set up.   
To run OIDC tests in a development environment, the environment variables `xdc_ClientId` and `xdc_ClientSecret` must be set.

### Building packages

In order to build RPM packages, two utility scripts are provided 
for the client and server: `fts-rest-client.sh` and `fts-rest-server.sh`.

The following example shows how to build server packages:
```shell
$ ./packaging/server/fts-rest-server.sh
$ tree "build/server/RPMS"
```

## Useful links

- Documentation: https://fts3-docs.web.cern.ch/fts3-docs/fts-rest/docs/index.html
- FTS Repository: https://fts-repo.web.cern.ch/fts-repo/
- Apache License, version 2.0: https://www.apache.org/licenses/LICENSE-2.0
- Support channels: fts-support@cern.ch
- Development team contact: fts-devel@cern.ch 


[1]: https://gitlab.cern.ch/fts/fts-rest
[2]: https://its.cern.ch/jira/browse/FTS-1496
[3]: https://fts-repo.web.cern.ch/fts-repo/el7/x86_64/
[4]: https://fts-repo.web.cern.ch/fts-repo/testing/el7/x86_64/
[5]: https://its.cern.ch/jira/projects/FTS/issues
[6]: https://nvie.com/posts/a-successful-git-branching-model/
[7]: https://gitlab.cern.ch/fts/fts-rest-flask/-/pipelines
[8]: https://docs.gitlab.com/ee/ci/yaml/#skipping-jobs
[9]: https://github.com/jazzband/pip-tools

[10]: https://fts3-docs.web.cern.ch/fts3-docs/fts-rest/docs/index.html
[11]: https://www.apache.org/licenses/LICENSE-2.0
