import logging
import sys
import json

from sqlalchemy import or_

import ckan.model as model

REQUESTS_HEADER = {'content-type': 'application/json',
                   'User-Agent': 'ckanext-qa commands'}


log = logging.getLogger(__name__)


def init_db():
    from ckanext.qa.model import init_tables
    init_tables(model.meta.engine)


def update(args, queue):
    from ckanext.qa import lib
    packages = []
    resources = []
    if len(args) > 0:
        for arg in args[0:]:
            # try arg as a group id/name
            group = model.Group.get(arg)
            if group and group.is_organization:
                # group.packages() is unreliable for an organization -
                # member objects are not definitive whereas owner_org, so
                # get packages using owner_org
                query = model.Session.query(model.Package)\
                    .filter(
                        or_(model.Package.state == 'active',
                            model.Package.state == 'pending'))\
                    .filter_by(owner_org=group.id)
                packages.extend(query.all())
                if not queue:
                    queue = 'bulk'
                continue
            elif group:
                packages.extend(group.packages())
                if not queue:
                    queue = 'bulk'
                continue
            # try arg as a package id/name
            pkg = model.Package.get(arg)
            if pkg:
                packages.append(pkg)
                if not queue:
                    queue = 'priority'
                continue
            # try arg as a resource id
            res = model.Resource.get(arg)
            if res:
                resources.append(res)
                if not queue:
                    queue = 'priority'
                continue
            else:
                log.error('Could not recognize as a group, package \
                                                or resource: %r', arg)
                sys.exit(1)
    else:
        # all packages
        pkgs = model.Session.query(model.Package)\
                    .filter_by(state='active')\
                    .order_by('name').all()
        packages.extend(pkgs)
        if not queue:
            queue = 'bulk'
    if packages:
        log.info('Datasets to QA: %d', len(packages))
    if resources:
        log.info('Resources to QA: %d', len(resources))
    if not (packages or resources):
        log.error('No datasets or resources to process')
        sys.exit(1)

    log.info('Queue: %s', queue)
    for package in packages:
        lib.create_qa_update_package_task(package, queue)
        log.info('Queuing dataset %s (%s resources)',
                        package.name, len(package.resources))

    for resource in resources:
        package = resource.resource_group.package
        log.info('Queuing resource %s/%s', package.name, resource.id)
        lib.create_qa_update_task(resource, queue)

    log.info('Completed queueing')

def view(package_ref=None):
    
    q = model.Session.query(model.TaskStatus).filter_by(task_type='qa')
    print ('QA records - %i TaskStatus rows' % q.count())
    print ('      across %i Resources' % q.distinct('entity_id').count())

    if package_ref:
        pkg = model.Package.get(package_ref)
        print ('Package %s %s' % (pkg.name, pkg.id))
        for res in pkg.resources:
            print ('Resource %s' % res.id)
            for row in q.filter_by(entity_id=res.id):
                print ('* %s = %r error=%r' % (row.key, row.value,
                                                row.error))

def migrate():
    q_status = model.Session.query(model.TaskStatus) \
        .filter_by(task_type='qa') \
        .filter_by(key='status')
    print ('* %s with "status" will be deleted e.g. %s' % (q_status.count(),
                                                            q_status.first()))
    q_failures = model.Session.query(model.TaskStatus) \
        .filter_by(task_type='qa') \
        .filter_by(key='openness_score_failure_count')
    print ('* %s with openness_score_failure_count to be deleted e.g.\n%s'\
        % (q_failures.count(), q_failures.first()))
    q_score = model.Session.query(model.TaskStatus) \
        .filter_by(task_type='qa') \
        .filter_by(key='openness_score')
    print ('* %s with openness_score to migrate e.g.\n%s' % \
        (q_score.count(), q_score.first()))
    q_reason = model.Session.query(model.TaskStatus) \
        .filter_by(task_type='qa') \
        .filter_by(key='openness_score_reason')
    print ('* %s with openness_score_reason to migrate e.g.\n%s' % \
        (q_reason.count(), q_reason.first()))
    input('Press Enter to continue')

    q_status.delete()
    model.Session.commit()
    print ('..."status" deleted')

    q_failures.delete()
    model.Session.commit()
    print ('..."openness_score_failure_count" deleted')

    for task_status in q_score:
        reason_task_status = q_reason \
            .filter_by(entity_id=task_status.entity_id) \
            .first()
        if reason_task_status:
            reason = reason_task_status.value
            reason_task_status.delete()
        else:
            reason = None

        task_status.key = 'status'
        task_status.error = json.dumps({
            'reason': reason,
            'format': None,
            'is_broken': None,
            })
        model.Session.commit()
    print ('..."openness_score" and "openness_score_reason" migrated')
    count = q_reason.count()
    q_reason.delete()
    model.Session.commit()
    print ('... %i remaining "openness_score_reason" deleted' % count)

    model.Session.flush()
    model.Session.remove()
    print ('Migration succeeded')

def clean():
    print ('Before:')
    view()

    q = model.Session.query(model.TaskStatus).filter_by(task_type='qa')
    q.delete()
    model.Session.commit()

    print ('After:')
    view()

def sniff(args):
    from ckanext.qa.sniff_format import sniff_file_format
    if len(args) < 1:
        print ('Not enough arguments', args)
        sys.exit(1)
    for filepath in args[0:]:
        format_ = sniff_file_format(filepath)
        if format_:
            print ('Detected as: %s - %s' % (format_['format'],
                                            filepath))
        else:
            print ('ERROR: Could not recognise format of: %s' % filepath)
