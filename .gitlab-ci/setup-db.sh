#!/bin/sh

curl -s -O https://gitlab.cern.ch/fts/fts3/-/raw/FTS-1914/src/db/schema/mysql/fts-schema-8.1.0.sql

mysql --user=root --password=ftsflaskroot --host=mariadb ftsflask < fts-schema-8.1.0.sql
echo "CREATE USER 'fts3'@'%';" | mysql --user=root --password=ftsflaskroot --host=mariadb
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'fts3'@'%' IDENTIFIED BY 'ftsflaskpass';" | mysql --user=root --password=ftsflaskroot --host=mariadb
