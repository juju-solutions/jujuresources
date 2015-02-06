from setuptools import setup
import os


version_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'VERSION'))
with open(version_file) as v:
    VERSION = v.read().strip()


SETUP = {
    'name': "jujuresources",
    'version': VERSION,
    'author': "Cory Johns",
    'author_email': "cory.johns@canonical.com",
    'url': "https://github.com/juju-solutions/jujuresources",
    'packages': [
        "jujuresources",
    ],
    'install_requires': [
        'pyaml',
    ],
    'entry_points': {
        'console_scripts': [
            'juju-resources = jujuresources.cli:resources',
        ],
        'jujuresources.subcommands': [
            'fetch = jujuresources.cli:fetch',
            'verify = jujuresources.cli:verify',
            'serve = jujuresources.cli:serve',
            'resource_path = jujuresources.cli:resource_path',
        ],
    },
    'license': "MIT License",
    'long_description': open('README.rst').read(),
    'description': 'Helpers for Juju Charms to load external resources',
}

try:
    from sphinx_pypi_upload import UploadDoc
    SETUP['cmdclass'] = {'upload_sphinx': UploadDoc}
except ImportError:
    pass

if __name__ == '__main__':
    setup(**SETUP)
