import pathlib

from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
with open(HERE / "robocop" / "version.py") as f:
    __version__ = f.read().split("=")[1].strip().strip('"')
CLASSIFIERS = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Programming Language :: Python :: 3.9
Programming Language :: Python :: 3.10
Programming Language :: Python :: 3.11
Framework :: Robot Framework
Framework :: Robot Framework :: Tool
Topic :: Software Development :: Testing
Topic :: Software Development :: Quality Assurance
Topic :: Utilities
Intended Audience :: Developers
""".strip().splitlines()
KEYWORDS = "robotframework automation testautomation testing linter qa"
DESCRIPTION = "Static code analysis tool (linter) for Robot Framework"
PROJECT_URLS = {
    "Documentation": "https://robocop.readthedocs.io/en/stable",
    "Issue tracker": "https://github.com/MarketSquare/robotframework-robocop/issues",
    "Source code": "https://github.com/MarketSquare/robotframework-robocop",
}


setup(
    name="robotframework-robocop",
    version=__version__,
    description=DESCRIPTION,
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/MarketSquare/robotframework-robocop",
    download_url="https://pypi.org/project/robotframework-robocop",
    author="Bartlomiej Hirsz, Mateusz Nojek",
    author_email="bartek.hirsz@gmail.com, matnojek@gmail.com",
    license="Apache License 2.0",
    platforms="any",
    classifiers=CLASSIFIERS,
    keywords=KEYWORDS,
    packages=["robocop"],
    project_urls=PROJECT_URLS,
    python_requires=">=3.9",
    include_package_data=True,
    install_requires=[
        "jinja2>=3.0,<4.0",
        "robotframework>=3.2.2,<7.2",
        "pathspec>=0.9,<0.13",
        "tomli>=2.0.0",
        "pytz>=2022.7",
        "python-dateutil>=2.8.2",
        "platformdirs>=3.2.0,<4.4.0",
    ],
    extras_require={
        "dev": [
            "ruff",
            "coverage",
            "pytest",
            "pyyaml",
            "pytest-benchmark",
            "nox",
        ],
        "doc": [
            "furo",
            "sphinx",
            "sphinx_design",
            "sphinx-copybutton",
            "sphinxemoji",
            "pygments",
        ],
    },
    entry_points={"console_scripts": ["robocop=robocop:run_robocop"]},
)
