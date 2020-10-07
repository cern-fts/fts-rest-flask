#!/bin/sh

# These files are needed for the docker build
echo Building fts-rest-flask:ci ...
cp ../pipcompile.sh ../pipsyncdev.sh ../dev-requirements.in ../requirements.in .
docker login gitlab-registry.cern.ch/fts/fts-rest-flask
docker build -t gitlab-registry.cern.ch/fts/fts-rest-flask:ci .
docker push  gitlab-registry.cern.ch/fts/fts-rest-flask:ci
rm pipcompile.sh pipsyncdev.sh dev-requirements.in requirements.in

echo Building fts-rest-flask:rpm ...
docker build  -t gitlab-registry.cern.ch/fts/fts-rest-flask:rpm . -f ./Dockerfile-rpm
docker push  gitlab-registry.cern.ch/fts/fts-rest-flask:rpm