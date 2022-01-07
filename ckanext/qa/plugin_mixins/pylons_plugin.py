# encoding: utf-8

from ckan import plugins as p


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)

    # IRoutes

    def before_map(self, map):
        # Link checker - deprecated
        res = 'ckanext.qa.controllers.pylons_controllers:LinkCheckerController'
        map.connect('qa_resource_checklink', '/qa/link_checker',
                    conditions=dict(method=['GET']),
                    controller=res,
                    action='check_link')
        return map
