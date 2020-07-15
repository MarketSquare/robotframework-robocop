import pathlib
from setuptools import find_packages, setup
from robocop.version import __version__


HERE = pathlib.Path(__file__).parent
README = (HERE / "README.rst").read_text()
CLASSIFIERS = """
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3.8
""".strip().splitlines()

setup(
    name =                          'robotframework-robocop',
    version =                       __version__,
    description =                   'Linter for Robot Framework',
    long_description =              README,
    long_description_content_type = "text/markdown",
    url =                           "https://github.com/bhirsz/robotframework-robocop",
    author =                        "Bartlomiej Hirsz, Mateusz Nojek",
    author_email =                  "bartek.hirsz@gmail.com, matnojek@gmail.com",
    license =                       "Apache License 2.0",
    platforms =                     "any",
    classifiers =                   CLASSIFIERS,
    packages =                      ['robocop'],
    include_package_data =          True,
    install_requires =              ['robotframework>=3.2.1'],
    entry_points =                  {'console_scripts':
                                         ['robocop=robocop:run_robocop']
                                    },
)
