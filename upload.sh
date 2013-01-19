#!/bin/sh

set -e

# if credentials are missing run:
# manage-credentials create -c ubuntu-dev-tools -l 2

NEWS="$1"

VERSION=`python -c "import sys; sys.path.append('src/tools'); import consts; print consts.appVersion"`
# Tool resides in package lptools.
lp-project-upload pogo $VERSION "pogo-$VERSION.tar.gz" $VERSION /dev/null "$NEWS"
