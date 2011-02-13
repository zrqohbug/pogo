#!/bin/sh

INSTALL_DIR="/usr/share/pogo"
MAN_DIR="/usr/share/man/man1"
BIN_DIR="/usr/bin"
APP_DIR="/usr/share/applications"
LOC_DIR="/usr/share/locale"
DOC_DIR="/usr/share/doc/pogo"
ICO_DIR="/usr/local/share/pixmaps"
VERSION=`cat control-install | grep "Version" | cut -d\  -f2`

# Make clean
find -type f -name "*.pyc" -exec rm -f {} \;
find -type f -name "*.pyo" -exec rm -f {} \;

mkdir -p pogo/DEBIAN
cp control-install pogo/DEBIAN/control

mkdir -p "pogo"$ICO_DIR
cp pix/pogo.png "pogo"$ICO_DIR

mkdir -p "pogo"$MAN_DIR
cp doc/pogo.1 "pogo"$MAN_DIR

mkdir -p "pogo"$INSTALL_DIR

cp -R src "pogo"$INSTALL_DIR"/"

# Resources
mkdir -p "pogo"$INSTALL_DIR"/res"
cp res/*.glade "pogo"$INSTALL_DIR"/res/"

mkdir -p "pogo"$INSTALL_DIR"/pix"
cp pix/*.png "pogo"$INSTALL_DIR"/pix/"

mkdir -p "pogo"$DOC_DIR
cp doc/COPYING "pogo"$DOC_DIR
cp doc/NEWS "pogo"$DOC_DIR
cp doc/README "pogo"$DOC_DIR

mkdir -p "pogo"$APP_DIR
cp res/*.desktop "pogo"$APP_DIR

mkdir -p "pogo"$BIN_DIR
cp pogo.py "pogo"$BIN_DIR"/pogo"

# Create locales
rm -rf locale
cd po
make dist
cd ..

# Copy locales
mkdir -p "pogo"$LOC_DIR
cp -R locale/* "pogo"$LOC_DIR

# Remove .svn directories
find "pogo" -type d -name ".svn" -exec rm -rf {} \; > /dev/null 2>&1

# Sources: Make sure to remove non-Python files
find "pogo"$INSTALL_DIR"/src" -type f ! -name "*.py" -exec rm -f {} \;

dpkg-deb --build pogo pogo-$VERSION.deb
rm -rf pogo