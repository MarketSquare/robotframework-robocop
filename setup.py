import pathlib
from setuptools import setup
from robocop.version import __version__

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.rst").read_text()
CLASSIFIERS = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
Framework :: Robot Framework
Framework :: Robot Framework :: Tool
Topic :: Software Development :: Testing
Topic :: Software Development :: Quality Assurance
Topic :: Utilities
Intended Audience :: Developers
""".strip().splitlines()

setup(
    name='robotframework-robocop',
    version=__version__,
    description='Static code analysis tool (linter) for Robot Framework',
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://github.com/MarketSquare/robotframework-robocop",
    author="Bartlomiej Hirsz, Mateusz Nojek",
    author_email="bartek.hirsz@gmail.com, matnojek@gmail.com",
    license="Apache License 2.0",
    platforms="any",
    classifiers=CLASSIFIERS,
    keywords='robotframework',
    packages=['robocop'],
    include_package_data=True,
    install_requires=['robotframework>=3.2.1'],
    extras_requires={
        'dev': ['pytest'],
        'doc': ['sphinx', 'sphinx_rtd_theme']
    },
    entry_points={'console_scripts': ['robocop=robocop:run_robocop']},
)
