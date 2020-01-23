# About the migration
The migration of [fts-rest](https://gitlab.cern.ch:8443/fts/fts-rest) has started after the decisions made in 
the [evaluation](https://its.cern.ch/jira/browse/FTS-1496).

The development is happening at fts-flask.cern.ch

# Gitlab CI
The current pipeline runs for every push in every branch:
- black: fails if the code hasn't been formatted with black
- pylint: fails if the code has syntax errors
- radon: fails if the code complexity is too high
- bandit: detects potential security issues in the code, but it's allowed to fail as there may be false positives
Merge requests will proceed only if the pipeline succeeds.
In case of emergency the pipeline can be [skipped](https://docs.gitlab.com/ee/ci/yaml/#skipping-jobs).

