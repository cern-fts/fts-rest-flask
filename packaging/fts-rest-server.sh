PREPDIR=~/fts-rest-server-1.0
mkdir -p $PREPDIR
cp ../LICENSE $PREPDIR
cp -r ../src/fts3rest $PREPDIR
cp fts-rest-server.spec ~/rpmbuild/SPECS
cd
tar -czf fts-rest-server-1.0.tar.gz fts-rest-server-1.0
mv fts-rest-server-1.0.tar.gz rpmbuild/SOURCES/
cd ~/rpmbuild/SPECS