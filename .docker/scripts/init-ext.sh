#!/usr/bin/env sh
##
# Install current extension.
#
set -e

. ${APP_DIR}/scripts/activate

pip install -r "dev-requirements.txt"
if [ -f "requirements-$PYTHON_VERSION.txt" ]; then
    pip install -r "requirements-$PYTHON_VERSION.txt"
else
    pip install -r "requirements.txt"
fi
pip install -r "${SRC_DIR}/ckanext-archiver/requirements.txt"
pip install -e .
installed_name=$(grep '^\s*name=' setup.py |sed "s|[^']*'\([-a-zA-Z0-9]*\)'.*|\1|")

# Validate that the extension was installed correctly.
if ! pip list | grep "$installed_name" > /dev/null; then echo "Unable to find the extension in the list"; exit 1; fi

. ${APP_DIR}/scripts/deactivate
