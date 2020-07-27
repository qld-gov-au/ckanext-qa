#!/bin/sh -e

# !/bin/bash
ver=$(python -c"import sys; print(sys.version_info.major)")
if [ $ver -eq 2 ]; then
    echo "python version 2 running nosetests"
    nosetests --with-pylons=subdir/test-core.ini --with-coverage --cover-package=ckanext.qa --cover-inclusive --cover-erase --cover-tests
elif [ $ver -eq 3 ]; then
    echo "python version 3 running pytest"
    pytest --ckan-ini=subdir/test-core.ini --cov=ckanext.qa ckanext/qa/tests
else
    echo "Unknown python version: $ver"
    exit 1
fi