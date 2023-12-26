import nox

UNIT_TEST_PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]
ROBOT_VERSIONS = ["3", "4", "5", "6", "7"]
nox.options.sessions = [
    "unit",
]


def install_dev_deps(session, robot_major_ver):
    session.install("-r", f"tests/rf_versions_matrix/requirements_rf{robot_major_ver}.txt")
    session.install(".[dev]")


def install_doc_deps(session, robot_major_ver):
    session.install("-r", f"tests/rf_versions_matrix/requirements_rf{robot_major_ver}.txt")
    session.install(".[doc]")


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
@nox.parametrize("rf", ROBOT_VERSIONS)
def unit(session, rf):
    install_dev_deps(session, rf)
    session.run("pytest", "tests")


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
@nox.parametrize("rf", ROBOT_VERSIONS)
def coverage(session, rf):
    install_dev_deps(session, rf)
    session.install("coverage")
    session.run("coverage", "run", "-a", "-m", "pytest")
    session.notify("coverage_report")


@nox.session
def coverage_report(session):
    session.run("coverage", "html")


@nox.session()
def docs(session):
    install_doc_deps(session, ROBOT_VERSIONS[-1])
    session.run("sphinx-build", "-a", "-E", "-b", "html", "docs", "docs/_build/")


@nox.session()
def benchmark(session):
    install_dev_deps(session, ROBOT_VERSIONS[-1])
    session.run(
        "pytest",
        "--benchmark-only",
        "--benchmark-enable",
        "--benchmark-save=benchmark_results",
        "--benchmark-save-data",
    )
