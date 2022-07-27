#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to generate a FTS-REST-Flask server tarball.
# Execute the script from the root of the git repository
# -------------------------------------------------------------------

VERSION=$(grep -m1 packaging/server/fts-rest-server.spec -e "^Version:" | awk {'print $2'})
printf "Version:\t%s\n" "${VERSION}"
DIST="fts-rest-server-${VERSION}"
mkdir -p "build/server/${DIST}"

# Copying files for dist
cp LICENSE "build/server/${DIST}"
cp -r src/fts3rest "build/server/${DIST}"

# Create tarball
tar -C "build/server/" -cvzf "build/server/${DIST}.tar.gz" --exclude="__pycache__" --exclude="*.pyc" "${DIST}"
rm -rf "build/server/${DIST}"

if [[ -z ${SILENT} ]]; then
  printf "Wrote:\t%s\n" "${PWD}/build/server/${DIST}.tar.gz"
fi
