#!/bin/sh

curl -O https://gitlab.cern.ch/fts/fts3/-/raw/master/src/db/schema/mysql/fts-schema-6.0.0.sql

mysql --user=root --password=asdf --host=mariadb ftsflask < fts-schema-6.0.0.sql
echo "CREATE USER 'ci'@'%';" | mysql --user=root --password=asdf --host=mariadb
echo "GRANT ALL PRIVILEGES ON ftsflask.* TO 'ci'@'%' IDENTIFIED BY 'asdf';" | mysql --user=root --password=asdf --host=mariadb