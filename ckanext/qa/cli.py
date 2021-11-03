import click
import ckanext.qa.commands as commands

def get_commands():

    @click.group()
    def qa():
        """Generates qa command"""
        pass

    @qa.command()
    def init_db():
        commands.init_db()
        click.secho(u'QA tables are setup', fg=u"green")

    @qa.command()
    @click.option('-q', '--queue')
    @click.argument('args', nargs=-1)
    def update(args, queue):
        commands.update(args, queue)

    return [qa]