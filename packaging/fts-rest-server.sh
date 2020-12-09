#!/bin/sh
set -e

# -------------------------------------------------------------------
# Utility script to help packaging the fts-rest-server.
# The script must be called from the packaging directory
# and expects an rpmdev tree already exists
# -------------------------------------------------------------------

# Setup
TMPDIR=$(mktemp -d /tmp/fts-rest-server-build_XXXXX)
VERSION=$(grep -m1 fts-rest-server.spec -e "^Version:" | awk {'print $2'})
DISTDIR=${TMPDIR}/fts-rest-server-${VERSION}
mkdir -p ${DISTDIR}
echo "Version: ${VERSION}"

# Copying files for dist
cp ../LICENSE ${DISTDIR}
cp -r ../src/fts3rest ${DISTDIR}

# Create tarball
tar -C ${TMPDIR} -czf fts-rest-server-${VERSION}.tar.gz fts-rest-server-${VERSION}/

# Copy spec file to rpmbuild
mv fts-rest-server-${VERSION}.tar.gz ~/rpmbuild/SOURCES/
cp fts-rest-server.spec ~/rpmbuild/SPECS

rm -rf ${TMPDIR}
echo "Created tarball: " ~/rpmbuild/SOURCES/fts-rest-server-${VERSION}.tar.gz
