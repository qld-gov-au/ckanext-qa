import datetime
import six
import uuid

from behave import when, then
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.web.steps import *  # noqa: F401, F403

# Monkey-patch Selenium 3 to handle Python 3.9
import base64
if not hasattr(base64, 'encodestring'):
    base64.encodestring = base64.encodebytes

# Monkey-patch Behaving to handle function rename
from behaving.web.steps import forms
if not hasattr(forms, 'fill_in_elem_by_name'):
    forms.fill_in_elem_by_name = forms.i_fill_in_field

dataset_default_schema = """
    {"fields": [
        {"format": "default", "name": "Game Number", "type": "integer"},
        {"format": "default", "name": "Game Length", "type": "integer"}
    ],
    "missingValues": ["Default schema"]
    }
"""

resource_default_schema = """
    {"fields": [
        {"format": "default", "name": "Game Number", "type": "integer"},
        {"format": "default", "name": "Game Length", "type": "integer"}
    ],
    "missingValues": ["Resource schema"]
    }
"""


@when(u'I take a debugging screenshot')
def debug_screenshot(context):
    """ Take a screenshot only if debugging is enabled in the persona.
    """
    if context.persona and context.persona.get('debug') == 'True':
        context.execute_steps(u"""
            When I take a screenshot
        """)


@when(u'I go to homepage')
def go_to_home(context):
    context.execute_steps(u"""
        When I visit "/"
    """)


@when(u'I go to register page')
def go_to_register_page(context):
    context.execute_steps(u"""
        When I go to homepage
        And I press "Register"
    """)


@when(u'I log in')
def log_in(context):
    context.execute_steps(u"""
        When I go to homepage
        And I expand the browser height
        And I press "Log in"
        And I log in directly
    """)


@when(u'I expand the browser height')
def expand_height(context):
    # Work around x=null bug in Selenium set_window_size
    context.browser.driver.set_window_rect(x=0, y=0, width=1024, height=3072)


@when(u'I log in directly')
def log_in_directly(context):
    """
    This differs to the `log_in` function above by logging in directly to a page where the user login form is presented
    :param context:
    :return:
    """

    assert context.persona, "A persona is required to log in, found [{}] in context. Have you configured the personas in before_scenario?".format(context.persona)
    context.execute_steps(u"""
        When I attempt to log in with password "$password"
        Then I should see an element with xpath "//*[@title='Log out']/i[contains(@class, 'fa-sign-out')]"
    """)


@when(u'I attempt to log in with password "{password}"')
def attempt_login(context, password):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "login" with "$name"
        And I fill in "password" with "{}"
        And I press the element with xpath "//button[contains(string(), 'Login')]"
    """.format(password))


@then(u'I should see the login form')
def login_link_visible(context):
    context.execute_steps(u"""
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"
    """)


@when(u'I go to dataset page')
def go_to_dataset_page(context):
    context.execute_steps(u"""
        When I visit "/dataset"
    """)


@when(u'I go to organisation page')
def go_to_organisation_page(context):
    context.execute_steps(u"""
        When I visit "/organization"
    """)


@when(u'I fill in "{name}" with "{value}" if present')
def fill_in_field_if_present(context, name, value):
    context.execute_steps(u"""
        When I execute the script "field = $('#field-{0}'); if (!field.length) field = $('#{0}'); if (!field.length) field = $('[name={0}]'); field.val('{1}'); field.keyup();"
    """.format(name, value))


@when(u'I clear the URL field')
def clear_url(context):
    context.execute_steps(u"""
        When I execute the script "$('a.btn-remove-url:contains(Clear)').click();"
    """)


@when(u'I fill in title with random text')
def title_random_text(context):
    assert context.persona
    context.execute_steps(u"""
        When I fill in "title" with "Test Title {0}"
        And I fill in "name" with "test-title-{0}" if present
        And I set "last_generated_title" to "Test Title {0}"
        And I set "last_generated_name" to "test-title-{0}"
    """.format(uuid.uuid4()))


@when(u'I select the "{licence_id}" licence')
def select_licence(context, licence_id):
    # Licence requires special interaction due to fancy JavaScript
    context.execute_steps(u"""
        When I execute the script "$('#field-license_id').val('{0}').trigger('change')"
    """.format(licence_id))


@when(u'I enter the resource URL "{url}"')
def enter_resource_url(context, url):
    if url != "default":
        context.execute_steps(u"""
            When I clear the URL field
            When I execute the script "$('#resource-edit [name=url]').val('{0}')"
        """.format(url))


@when(u'I fill in default dataset fields')
def fill_in_default_dataset_fields(context):
    context.execute_steps(u"""
        When I fill in title with random text
        And I fill in "notes" with "Description"
        And I fill in "version" with "1.0"
        And I fill in "author_email" with "test@me.com"
        And I select the "other-open" licence
        And I fill in "de_identified_data" with "NO" if present
    """)


@when(u'I fill in default resource fields')
def fill_in_default_resource_fields(context):
    context.execute_steps(u"""
        When I fill in "name" with "Test Resource"
        And I fill in "description" with "Test Resource Description"
        And I fill in "size" with "1024" if present
    """)


@when(u'I fill in link resource fields')
def fill_in_default_link_resource_fields(context):
    context.execute_steps(u"""
        When I enter the resource URL "https://example.com"
        And I execute the script "document.getElementById('field-format').value='HTML'"
        And I fill in "size" with "1024" if present
    """)


@when(u'I upload "{file_name}" of type "{file_format}" to resource')
def upload_file_to_resource(context, file_name, file_format):
    context.execute_steps(u"""
        When I execute the script "$('#resource-upload-button').trigger(click);"
        And I attach the file "{file_name}" to "upload"
        # Don't quote the injected string since it can have trailing spaces
        And I execute the script "document.getElementById('field-format').value='{file_format}'"
        And I fill in "size" with "1024" if present
    """.format(file_name=file_name, file_format=file_format))


@when(u'I show the non-JavaScript schema fields')
def reveal_non_js_schema_fields(context):
    context.execute_steps(u"""
        When I execute the script "$('#resource-schema-buttons ~ div.form-group').attr('style', '')"
    """)


@when(u'I set the resource schema to the dataset default')
def set_resource_schema_to_dataset_default(context):
    _enter_manual_schema(context, dataset_default_schema)


# Enter a JSON schema value
# This can require JavaScript interaction, and doesn't fit well into
# a step invocation due to all the double quotes.
def _enter_manual_schema(context, schema_json):
    # Click the button to select manual JSON input if it exists
    context.execute_steps(u"""
        When I execute the script "$('a.btn[title*=JSON]:contains(JSON)').click();"
    """)
    # Call function directly so we can properly quote our parameter
    forms.fill_in_elem_by_name(context, "schema_json", schema_json)


# Parse a "key=value::key2=value2" parameter string and return an iterator of (key, value) pairs.
def _parse_params(param_string):
    params = {}
    for param in param_string.split("::"):
        entry = param.split("=", 1)
        params[entry[0]] = entry[1] if len(entry) > 1 else ""
    return six.iteritems(params)


def _create_dataset_from_params(context, params):
    context.execute_steps(u"""
        When I visit "/dataset/new"
        And I fill in default dataset fields
    """)
    if 'private' not in params:
        params = params + "::private=False"
    for key, value in _parse_params(params):
        if key == "name":
            # 'name' doesn't need special input, but we want to remember it
            context.execute_steps(u"""
                When I set "last_generated_name" to "{0}"
            """.format(value))

        # Don't use elif here, we still want to type 'name' as usual
        if key == "owner_org":
            # Owner org uses UUIDs as its values, so we need to rely on displayed text
            context.execute_steps(u"""
                When I select by text "{1}" from "{0}"
            """.format(key, value))
        elif key in ["update_frequency", "request_privacy_assessment", "private"]:
            context.execute_steps(u"""
                When I select "{1}" from "{0}"
            """.format(key, value))
        elif key == "license_id":
            context.execute_steps(u"""
                When I select the "{0}" licence
            """.format(value))
        elif key == "schema_json":
            if value == "default":
                value = dataset_default_schema
            _enter_manual_schema(context, value)
        else:
            context.execute_steps(u"""
                When I fill in "{0}" with "{1}" if present
            """.format(key, value))
    context.execute_steps(u"""
        When I take a debugging screenshot
        And I press "Add Data"
        Then I should see "Add New Resource"
    """)


@when(u'I create a dataset with key-value parameters "{params}"')
def create_dataset_from_params(context, params):
    _create_dataset_from_params(context, params)
    context.execute_steps(u"""
        When I go to dataset "$last_generated_name"
    """)


@when(u'I create a dataset and resource with key-value parameters "{params}" and "{resource_params}"')
def create_dataset_and_resource_from_params(context, params, resource_params):
    _create_dataset_from_params(context, params)
    context.execute_steps(u"""
        When I create a resource with key-value parameters "{0}"
        Then I should see "Data and Resources"
    """.format(resource_params))


# Creates a resource using default values apart from the ones specified.
# The browser should already be on the create/edit resource page.
@when(u'I create a resource with key-value parameters "{resource_params}"')
def create_resource_from_params(context, resource_params):
    context.execute_steps(u"""
        When I fill in default resource fields
        And I fill in link resource fields
    """)
    for key, value in _parse_params(resource_params):
        if key == "url":
            context.execute_steps(u"""
                When I enter the resource URL "{0}"
            """.format(value))
        elif key == "upload":
            if value == "default":
                value = "test_game_data.csv"
            context.execute_steps(u"""
                When I clear the URL field
                And I execute the script "$('#resource-upload-button').click();"
                And I attach the file "{0}" to "upload"
            """.format(value))
        elif key == "format":
            context.execute_steps(u"""
                When I execute the script "document.getElementById('field-format').value='{0}'"
            """.format(value))
        elif key == "schema":
            if value == "default":
                value = resource_default_schema
            _enter_manual_schema(context, value)
        else:
            context.execute_steps(u"""
                When I fill in "{0}" with "{1}" if present
            """.format(key, value))
    context.execute_steps(u"""
        When I take a debugging screenshot
        And I press the element with xpath "//form[contains(@class, 'resource-form')]//button[contains(@class, 'btn-primary')]"
        And I take a debugging screenshot
    """)


@when(u'I reload page every {seconds:d} seconds until I see an element with xpath "{xpath}" but not more than {reload_times:d} times')
def reload_page_every_n_until_find(context, xpath, seconds=5, reload_times=5):
    for _ in range(reload_times):
        element = context.browser.is_element_present_by_xpath(
            xpath, wait_time=seconds
        )
        if element:
            assert element, 'Element with xpath "{}" was found'.format(xpath)
            return
        else:
            print("Element with xpath '{}' was not found, reloading at {}...".format(xpath, datetime.datetime.now()))
            context.browser.reload()

    assert False, 'Element with xpath "{}" was not found'.format(xpath)


@then(u'I should see data usability rating {score}')
def data_usability_rating_visible(context, score):
    context.execute_steps(u"""
        Then I should see an element with xpath "//div[contains(@class, 'openness-{0}')]"
    """.format(score))
