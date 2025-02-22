#!/bin/sh -e
flake8 --version
# stop the build if there are Python syntax errors or undefined names
flake8 . --count --select=E901,E999,F821,F822,F823 --show-source --statistics --exclude ckan,ckanext-archiver,ckanext-report
# exit-zero treats all errors as warnings.  The GitHub editor is 127 chars wide
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude ckan,ckanext-archiver,ckanext-report