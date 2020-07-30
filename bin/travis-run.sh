#!/bin/bash
set -ex

ver=$(python -c"import sys; print(sys.version_info.major)")
testFramework=nose
if [ "${CKAN_BRANCH}dd" == 'dd' ]; then
  if [ "$CKANVERSION" == '2.9' ]
    then
       testFramework=pytest
    else
        testFramework=nose
    fi
elif [ "$CKAN_BRANCH" == 'master' ]; then
       testFramework=pytest
fi

if [[ $ver -eq 3  ||  "$testFramework" == "pytest" ]]; then
    echo "python version 3 or 2.9+ ckan running pytest"
    pytest --ckan-ini=subdir/test.ini --cov=ckanext.qa ckanext/qa/tests
else
    echo "python version 2 running nosetests"
    nosetests --with-pylons=subdir/test-core.ini --with-coverage --cover-package=ckanext.qa --cover-inclusive --cover-erase --cover-tests
fi