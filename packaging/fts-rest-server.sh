PREPDIR=~/fts-rest-server-0.2
mkdir -p $PREPDIR
cp ../LICENSE $PREPDIR
cp -r ../src/fts3rest $PREPDIR
cp fts-rest-server.spec ~/rpmbuild/SPECS
cd
tar -czf fts-rest-server-0.2.tar.gz fts-rest-server-0.2
mv fts-rest-server-0.2.tar.gz rpmbuild/SOURCES/
cd ~/rpmbuild/SPECS