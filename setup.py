# encoding: utf-8
from setuptools import setup, find_packages

setup(
    name='ckanext-qa',
    version='2.0',
    description='Quality Assurance plugin for CKAN',
    long_description='',
    classifiers=[],
    keywords='',
    author='Open Knowledge Foundation, Cabinet Office & contributors',
    author_email='info@okfn.org',
    url='http://ckan.org/wiki/Extensions',
    license='mit',
    packages=find_packages(exclude=['tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # CKAN extensions should not list dependencies here, but in a separate
        # ``requirements.txt`` file.
        #
        # http://docs.ckan.org/en/latest/extensions/best-practices.html#add-third-party-libraries-to-requirements-txt
    ],
    tests_require=[
        # CKAN extensions should not list dependencies here, but in a separate
        # ``dev-requirements.txt`` file.
        #
        # http://docs.ckan.org/en/latest/extensions/best-practices.html#add-third-party-libraries-to-requirements-txt
    ],
    entry_points='''
    [ckan.plugins]
    qa=ckanext.qa.plugin:QAPlugin

    [babel.extractors]
    ckan = ckan.lib.extract:extract_ckan
    ''',
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
