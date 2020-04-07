#!/bin/sh

curl -O https://gitlab.cern.ch/fts/fts3/-/raw/fts-oidc-integration/src/db/schema/mysql/fts-schema-5.0.0.sql
curl -O https://gitlab.cern.ch/fts/fts3/-/raw/fts-oidc-integration/src/db/schema/mysql/fts-diff-6.0.0.sql
mysql --user=root --password=asdf --host=mariadb ftsflask < fts-schema-5.0.0.sql
mysql --user=root --password=asdf --host=mariadb ftsflask < fts-diff-6.0.0.sql
mysql --user=root --password=asdf --host=mariadb  < .gitlab-ci/db.sql