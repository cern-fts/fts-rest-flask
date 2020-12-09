#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to help packaging the fts-rest-client.
# The script must be called from the packaging directory
# and expects an rpmdev tree already exists
# -------------------------------------------------------------------

# Setup
TMPDIR=$(mktemp -d /tmp/fts-rest-client-build_XXXXX)
VERSION=$(grep -m1 fts-rest-client.spec -e "^Version:" | awk {'print $2'})
DISTDIR=${TMPDIR}/fts-rest-client-${VERSION}
mkdir -p ${DISTDIR}/src
echo "Version: ${VERSION}"

# Copying files for dist
cp ../LICENSE ${DISTDIR}
cp ../setup.py ${DISTDIR}
cp -r ../src/cli ../src/fts3 ${DISTDIR}/src

# Create tarball
tar -C ${TMPDIR} -czf fts-rest-client-${VERSION}.tar.gz fts-rest-client-${VERSION}/

# Place files in
mv fts-rest-client-${VERSION}.tar.gz ~/rpmbuild/SOURCES/
cp fts-rest-client.spec ~/rpmbuild/SPECS

rm -rf ${TMPDIR}
echo "Created tarball:" ~/rpmbuild/SOURCES/fts-rest-client-${VERSION}.tar.gz
