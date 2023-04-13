from behave import step
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.web.steps import *  # noqa: F401, F403
from behaving.web.steps.url import when_i_visit_url
import uuid


# Monkey-patch Selenium 3 to handle Python 3.9
import base64
try:
    from base64 import encodestring
except Exception:
    base64.encodestring = base64.encodebytes


@step(u'I go to homepage')
def go_to_home(context):
    when_i_visit_url(context, '/')


@step(u'I log in')
def log_in(context):
    assert context.persona
    context.execute_steps(u"""
        When I go to homepage
        And I resize the browser to 1024x2048
        And I click the link with text that contains "Log in"
        And I log in directly
    """)


@step(u'I log in directly')
def log_in_directly(context):
    """
    This differs to the `log_in` function above by logging in directly to a page where the user login form is presented
    :param context:
    :return:
    """

    assert context.persona
    context.execute_steps(u"""
        When I attempt to log in with password "$password"
        Then I should see an element with xpath "//a[@title='Log out']"
    """)


@step(u'I attempt to log in with password "{password}"')
def attempt_login(context, password):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "login" with "$name"
        And I fill in "password" with "{}"
        And I press the element with xpath "//button[contains(string(), 'Login')]"
    """.format(password))


@step(u'I should see a login link')
def login_link_visible(context):
    context.execute_steps(u"""
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"
    """)


@step(u'I go to dataset page')
def go_to_dataset_page(context):
    when_i_visit_url(context, '/dataset')


@step(u'I go to organisation page')
def go_to_organisation_page(context):
    when_i_visit_url(context, '/organization')


@step(u'I go to register page')
def go_to_register_page(context):
    when_i_visit_url(context, '/user/register')


@step(u'I fill in title with random text')
def title_random_text(context):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "title" with "Test Title {0}"
    """.format(uuid.uuid4()))


@step(u'I create a dataset with license {license} and resource file {file}')
def create_dataset_json(context, license, file):
    create_dataset(context, license, 'JSON', file)


@step(u'I create a dataset with license {license} and {file_format} resource file {file}')
def create_dataset(context, license, file_format, file):
    assert context.persona
    context.execute_steps(u"""
        When I visit "dataset/new"
        And I fill in title with random text
        And I fill in "notes" with "Description"
        And I fill in "version" with "1.0"
        And I fill in "author_email" with "test@me.com"
        And I execute the script "document.getElementById('field-license').value={license}"
        Then I press "Add Data"
        And I execute the script "button = document.getElementById('resource-upload-button'); if (button) button.click();"
        And I attach the file {file} to "upload"
        And I fill in "name" with "Test Resource"
        And I execute the script "document.getElementById('field-format').value={file_format}"
        And I fill in "description" with "Test Resource Description"
        And I press "Finish"
    """.format(license=license, file=file, file_format=file_format))


@step(u'I should see data usability rating {score}')
def data_usability_rating_visible(context, score):
    context.execute_steps(u"""
        Then I should see an element with xpath "//div[contains(@class, 'openness-{0}')]"
    """.format(score))
