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

    return [qa]