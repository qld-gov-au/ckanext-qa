import logging

import ckan.plugins as plugins
from ckan.plugins.interfaces import Interface

log = logging.getLogger(__name__)


class IQA(Interface):
    """
    Interface for other plugins to hook into and apply their own custom resource score before it's saved
    """

    @classmethod
    def custom_resource_score(cls, resource, resource_score):
        result = None
        for observer in plugins.PluginImplementations(cls):
            try:
                result = observer.custom_resource_score(resource, resource_score)
            except Exception, ex:
                log.exception(ex)
                # We reraise all exceptions so they are obvious there
                # is something wrong
                raise
        return result
