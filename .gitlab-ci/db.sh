#!/bin/sh

curl -O https://gitlab.cern.ch/fts/fts3/-/raw/fts-oidc-integration/src/db/schema/mysql/fts-schema-5.0.0.sql
curl -O https://gitlab.cern.ch/fts/fts3/-/raw/fts-oidc-integration/src/db/schema/mysql/fts-diff-6.0.0.sql
mysql -u=root -p=asdf -h=centos__mariadb ftsflask < .gitlab-ci/db.sql
mysql -u=root -p=asdf -h=centos__mariadb ftsflask < fts-schema-5.0.0.sql
mysql -u=root -p=asdf -h=centos__mariadb ftsflask < fts-diff-6.0.0.sql
