PREPDIR=~/fts-rest-client-0.1
mkdir -p $PREPDIR
cp ../LICENSE $PREPDIR
cp ../setup.py $PREPDIR
cp -r ../src/cli ../src/fts3 $PREPDIR
cp fts-rest-client.spec ~/rpmbuild/SPECS
cd
tar -czf fts-rest-client-0.1.tar.gz fts-rest-client-0.1
mv fts-rest-client-0.1.tar.gz rpmbuild/SOURCES/
cd ~/rpmbuild/SPECS