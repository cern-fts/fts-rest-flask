#!/bin/sh
pip-compile --generate-hashes requirements.in
pip-compile --generate-hashes dev-requirements.in
pip-compile requirements.in --output-file install_requires.txt
