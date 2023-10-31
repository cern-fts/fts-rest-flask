#!/bin/sh

curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/FTS-1925_token_project/src/db/schema/mysql/fts-schema-9.0.0.sql

mysql --user=root --password=ftsflaskroot --host=mysqldb ftsflask < fts-schema-9.0.0.sql
echo "CREATE USER 'fts3'@'%' IDENTIFIED BY 'ftsflaskpass';" | mysql --user=root --password=ftsflaskroot --host=mysqldb
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'fts3'@'%';" | mysql --user=root --password=ftsflaskroot --host=mysqldb
