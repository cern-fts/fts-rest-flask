#!/bin/sh

docker login gitlab-registry.cern.ch/fts/fts-rest-flask
docker build -t gitlab-registry.cern.ch/fts/fts-rest-flask:ci .
docker push  gitlab-registry.cern.ch/fts/fts-rest-flask:ci
