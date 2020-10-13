PREPDIR=~/fts-rest-client-0.2
mkdir -p $PREPDIR/src
cp ../LICENSE $PREPDIR
cp ../setup.py $PREPDIR
cp -r ../src/cli ../src/fts3 $PREPDIR/src
cp fts-rest-client.spec ~/rpmbuild/SPECS
cd
tar -czf fts-rest-client-0.2.tar.gz fts-rest-client-0.2
mv fts-rest-client-0.2.tar.gz rpmbuild/SOURCES/
cd ~/rpmbuild/SPECS