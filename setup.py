import pathlib
from setuptools import setup
from robocop.version import __version__

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
CLASSIFIERS = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Programming Language :: Python :: 3.9
Framework :: Robot Framework
Framework :: Robot Framework :: Tool
Topic :: Software Development :: Testing
Topic :: Software Development :: Quality Assurance
Topic :: Utilities
Intended Audience :: Developers
""".strip().splitlines()
KEYWORDS = ('robotframework automation testautomation testing linter qa')
DESCRIPTION = ('Static code analysis tool (linter) for Robot Framework')

setup(
    name         = 'robotframework-robocop',
    version      = __version__,
    description  = DESCRIPTION,
    long_description = README,
    long_description_content_type = 'text/markdown',
    url          = 'https://github.com/MarketSquare/robotframework-robocop',
    download_url = 'https://pypi.org/project/robotframework-robocop',
    author       = 'Bartlomiej Hirsz, Mateusz Nojek',
    author_email = 'bartek.hirsz@gmail.com, matnojek@gmail.com',
    license      = 'Apache License 2.0',
    platforms    = 'any',
    classifiers  = CLASSIFIERS,
    keywords     = KEYWORDS,
    packages     = ['robocop'],
    include_package_data = True,
    install_requires = ['robotframework>=3.2.2', 'toml>=0.10.2'],
    extras_requires = {
        'dev': ['pytest', 'pyyaml', 'tox'],
        'doc': ['sphinx', 'sphinx_rtd_theme']
    },
    entry_points = {'console_scripts': ['robocop=robocop:run_robocop']}
)
