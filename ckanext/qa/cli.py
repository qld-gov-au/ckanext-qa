# encoding: utf-8

import click
import ckanext.qa.commands as commands


def get_commands():

    @click.group()
    def qa():
        """Generates qa command"""
        pass

    @qa.command()
    def init_db():
        """Creates the database tables that QA expects for storing results"""
        commands.init_db()
        click.secho(u'QA tables are setup', fg=u"green")

    @qa.command()
    @click.option('-q', '--queue')
    @click.argument('args', nargs=-1)
    def update(args, queue):
        """QA analysis on all resources in a given dataset, or on all
           datasets if no dataset given"""
        commands.update(args, queue)

    @qa.command()
    @click.argument('package_ref', required=False)
    def view(package_ref):
        """See package score information"""
        if package_ref:
            commands.view(package_ref)
        else:
            commands.view()

    @qa.command()
    def migrate():
        """ Migrates the way results are stored in task_status,
            with commit 6f63ab9e 20th March 2013
            (from key='openness_score'/'openness_score_failure_count'
            to key='status')"""
        commands.migrate()

    @qa.command()
    def clean():
        """Remove all package score information"""
        commands.clean()

    @qa.command()
    @click.argument('args', nargs=-1)
    def sniff(args):
        """Opens the file and determines its type by the contents"""
        commands.sniff(args)

    return [qa]
