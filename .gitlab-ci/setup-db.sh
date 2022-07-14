#!/bin/sh

curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/master/src/db/schema/mysql/fts-schema-7.0.0.sql
curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/develop/src/db/schema/mysql/fts-diff-8.0.0.sql

mysql --user=root --password=ftsflaskroot --host=mariadb ftsflask < fts-schema-7.0.0.sql
mysql --user=root --password=ftsflaskroot --host=mariadb ftsflask < fts-diff-8.0.0.sql
echo "CREATE USER 'fts3'@'%';" | mysql --user=root --password=ftsflaskroot --host=mariadb
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'fts3'@'%' IDENTIFIED BY 'ftsflaskpass';" | mysql --user=root --password=ftsflaskroot --host=mariadb
