# encoding: utf-8

import logging

import ckan.plugins as p

from .cli import commands


class QACommand(p.toolkit.CkanCommand):
    """
    QA analysis of CKAN resources

    Usage::

        paster qa init
           - Creates the database tables that QA expects for storing
           results

        paster qa [options] update [dataset/group name/id]
           - QA analysis on all resources in a given dataset, or on all
           datasets if no dataset given

        paster qa sniff {filepath}
           - Opens the file and determines its type by the contents

        paster qa view [dataset name/id]
           - See package score information

        paster qa clean
           - Remove all package score information

        paster qa migrate1
           - Migrates the way results are stored in task_status,
             with commit 6f63ab9e 20th March 2013
             (from key='openness_score'/'openness_score_failure_count' to
              key='status')

    The commands should be run from the ckanext-qa directory and expect
    a development.ini file to be present. Most of the time you will
    specify the config explicitly though::

        paster qa update --config=<path to CKAN config file>
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__
    min_args = 0

    def __init__(self, name):
        super(QACommand, self).__init__(name)
        self.parser.add_option('-q', '--queue',
                               action='store',
                               dest='queue',
                               help='Send to a particular queue')

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print(QACommand.__doc__)
            return

        cmd = self.args[0]
        self._load_config()

        # Now we can import ckan and create logger, knowing that loggers
        # won't get disabled
        self.log = logging.getLogger('ckanext.qa')

        if cmd == 'update':
            commands.update(self.args, self.options.queue)
        elif cmd == 'sniff':
            commands.sniff(self.args)
        elif cmd == 'view':
            if len(self.args) == 2:
                commands.view(self.args[1])
            else:
                commands.view()
        elif cmd == 'clean':
            commands.clean()
        elif cmd == 'migrate1':
            commands.migrate()
        elif cmd == 'init':
            commands.init_db()
        else:
            self.log.error('Command "%s" not recognized' % (cmd,))
