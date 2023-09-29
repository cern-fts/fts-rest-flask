#!/bin/sh

curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/develop/src/db/schema/mysql/fts-schema-8.0.1.sql
curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/develop/src/db/schema/mysql/fts-diff-8.1.0.sql
curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/FTS-1829_scitags/src/db/schema/mysql/fts-diff-8.2.0.sql

mysql --user=root --password=ftsflaskroot --host=mysqldb ftsflask < fts-schema-8.0.1.sql
mysql --user=root --password=ftsflaskroot --host=mysqldb ftsflask < fts-diff-8.1.0.sql
echo "CREATE USER 'fts3'@'%' IDENTIFIED BY 'ftsflaskpass';" | mysql --user=root --password=ftsflaskroot --host=mysqldb
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'fts3'@'%';" | mysql --user=root --password=ftsflaskroot --host=mysqldb
