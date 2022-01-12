# encoding: utf-8

from flask import Blueprint

from . import check_link


qa = Blueprint(
    u'qa',
    __name__
)

qa.add_url_rule(
    '/qa/link_checker', 'qa_resource_checklink', methods=('GET',), view_func=check_link
)


def get_blueprints():
    return [qa]
