#!/usr/bin/env sh
##
# Initialise CKAN data for testing.
#
set -e

. "${APP_DIR}"/bin/activate
CLICK_ARGS="--yes" ckan_cli db clean
ckan_cli db init

# Initialise the archiver database tables
ckan_cli archiver init

# Initialise the reporting database tables
ckan_cli report initdb

# Initialise the QA database tables
ckan_cli qa init
