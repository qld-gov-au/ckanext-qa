#!/bin/bash
set -ex
# please start up docker via
# docker run -it -v "`pwd`":/build ubuntu:bionic /bin/bash
# cd /build bash -x  /build/bin/localPdev.sh



apt-get update
apt-get install -y sudo systemd postgresql-10 git python python-pip redis-server
/etc/init.d/postgresql start
redis-server &

pip install -U pip wheel

export CKAN_GIT_REPO=ckan/ckan
export CKANVERSION=2.8
export ARCHIVER_GIT_REPO=ckan
export ARCHIVER_BRANCH=master
export REPORT_GIT_REPO=datagovuk
export REPORT_BRANCH=master

bash -x bin/travis-build.bash

bash -x bin/travis-run.sh