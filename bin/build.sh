#!/usr/bin/env bash
##
# Build site in CI.
#
set -ex

# Process Docker Compose configuration. This is used to avoid multiple
# docker-compose.yml files.
# Remove lines containing '###'.
# Uncomment lines containing '##'.
sed -e "/###/d" docker-compose-template.yml | \
sed -e "s/##//" \
> docker-compose.yml

# Pull the latest images.
ahoy pull

PYTHON_VERSION=py3
PYTHON=python3
SOLR_VERSION=9

if [ "$CKAN_VERSION" = "2.9" ]; then
    SOLR_VERSION=8
fi

sed "s|{CKAN_VERSION}|$CKAN_VERSION|g" .docker/Dockerfile-template.ckan \
    | sed "s|{PYTHON_VERSION}|$PYTHON_VERSION|g" \
    | sed "s|{PYTHON}|$PYTHON|g" \
    > .docker/Dockerfile.ckan

export SOLR_VERSION
ahoy build
