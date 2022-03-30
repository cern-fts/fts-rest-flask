#!/bin/bash

FILENAME=$(readlink -f "$0")
PROJECT_DIR="${FILENAME%fts-rest-flask*}fts-rest-flask"

source "${PROJECT_DIR}/venv/bin/activate"
export PYTHONPATH="${PROJECT_DIR}/src:${PROJECT_DIR}/src/fts3rest"
export FTS3TESTCONFIG="${PROJECT_DIR}/src/fts3rest/fts3rest/tests/fts3testconfig"

pytest fts3rest/tests/functional/ -x
