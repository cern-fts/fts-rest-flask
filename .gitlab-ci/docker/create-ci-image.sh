#!/bin/sh

# These files are needed for the docker build
echo "Building fts-rest-flask:ci..."
cp -v ../../pipcompile.sh  ../../requirements.in ../../dev-requirements.in .

docker build -t gitlab-registry.cern.ch/fts/fts-rest-flask:ci .
docker login gitlab-registry.cern.ch/fts/fts-rest-flask
docker push gitlab-registry.cern.ch/fts/fts-rest-flask:ci

rm -v pipcompile.sh requirements.in dev-requirements.in
