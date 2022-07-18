import mock


def setup():
    # Register a mock translator instead of having ckan domain translations defined
    try:
        from ckan.lib.cli import MockTranslator
        patcher = mock.patch('pylons.i18n.translation._get_translator', return_value=MockTranslator())
        patcher.start()
    except ImportError:
        # if Pylons isn't present, we don't need it
        pass


def teardown():
    mock.patch.stopall()
