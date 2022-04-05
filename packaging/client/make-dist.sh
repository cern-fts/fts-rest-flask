#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to generate FTS-REST-Flask client tarball.
# Execute the script from the root of the git repository
# -------------------------------------------------------------------

VERSION=$(grep -m1 packaging/client/fts-rest-client.spec -e "^Version:" | awk {'print $2'})
printf "Version:\t%s\n" "${VERSION}"
DIST="fts-rest-client-${VERSION}"
mkdir -p "build/client/${DIST}/src"

# Copying files for dist
cp LICENSE setup.py setup.cfg "build/client/${DIST}"
cp -r src/cli src/fts3 "build/client/${DIST}/src"

# Create tarball
tar -C "build/client/" -cvzf "build/client/${DIST}.tar.gz" "${DIST}"
rm -rf "build/client/${DIST}"

if [[ -z ${SILENT} ]]; then
  printf "Wrote:\t%s\n" "${PWD}/build/client/${DIST}.tar.gz"
fi
