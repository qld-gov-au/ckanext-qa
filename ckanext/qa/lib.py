# encoding: utf-8

import json
import logging
import os
import re

from ckan.plugins.toolkit import config, get_action

log = logging.getLogger(__name__)

_RESOURCE_FORMAT_SCORES = None


def resource_format_scores():
    ''' Returns the resource formats scores as a dict keyed by format shortname
    (usually extension)

    :param key:  format shortname (usually extension) as defined in ckan's
                 resource_format.json
    :param value:  string
    :returns: openness score (int) - assuming it is accessible and has an open
              licence

    Fuller description of the fields are described in
    `ckan/config/resource_formats.json`.
    '''
    global _RESOURCE_FORMAT_SCORES
    if not _RESOURCE_FORMAT_SCORES:
        _RESOURCE_FORMAT_SCORES = {}
        json_filepath = config.get('qa.resource_format_openness_scores_json')
        import ckanext.qa.plugin
        if not json_filepath:
            json_filepath = os.path.join(
                os.path.dirname(os.path.realpath(ckanext.qa.plugin.__file__)),
                'resource_format_openness_scores.json'
            )
        with open(json_filepath) as format_file:
            try:
                file_resource_formats = json.loads(format_file.read())
            except ValueError as e:
                # includes simplejson.decoder.JSONDecodeError
                raise ValueError('Invalid JSON syntax in %s: %s' %
                                 (json_filepath, e))

            for format_line in file_resource_formats:
                if format_line[0] == '_comment':
                    continue
                format_, score = format_line
                if not isinstance(score, int):
                    raise ValueError('Score must be integer in %s: %s: %r'
                                     % json_filepath, format_, score)
                if format_ in _RESOURCE_FORMAT_SCORES:
                    raise ValueError('Duplicate resource format '
                                     'identifier in %s: %s' %
                                     (json_filepath, format_))
                _RESOURCE_FORMAT_SCORES[format_] = score

    return _RESOURCE_FORMAT_SCORES


def munge_format_to_be_canonical(format_name):
    '''Tries some things to help try and get a resource format to match one of
    the canonical ones
    '''
    format_name = format_name.strip().lower()
    if format_name.startswith('.'):
        format_name = format_name[1:]
    return re.sub('[^a-z/+]', '', format_name)


def get_job_apitoken():
    """ Returns the API Token for authentication.

    Job actions require an authenticated user to perform the actions. This
    method returns the api_token set in the config file and defaults to the
    site_user.
    """
    api_token = config.get('ckan.qa.api_token', None)
    if api_token:
        return api_token

    site_user = get_action('get_site_user')({'ignore_auth': True}, {})
    return site_user["apikey"]
