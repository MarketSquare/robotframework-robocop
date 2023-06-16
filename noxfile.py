import nox

UNIT_TEST_PYTHON_VERSIONS = ["3.7", "3.8", "3.9", "3.10", "3.11"]
nox.options.sessions = [
    "unit",
]
# TODO: Add better session names for easier control


def install_dev_deps(session, robot_major_ver):
    session.install("-r", f"tests/packages/rf-stable{robot_major_ver}/requirements.txt")
    session.install(".[dev]")


def install_doc_deps(session, robot_major_ver):
    session.install("-r", f"tests/packages/rf-stable{robot_major_ver}/requirements.txt")
    session.install(".[doc]")


@nox.session(python=UNIT_TEST_PYTHON_VERSIONS)
@nox.parametrize("rf", ["3", "4", "5", "6"])
def unit(session, rf):
    install_dev_deps(session, rf)
    session.run("pytest", "tests")


@nox.session()
def coverage(session):
    install_dev_deps(session, "5")
    session.install("coverage")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "html")


@nox.session()
def docs(session):
    install_doc_deps(session, "5")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build/")


@nox.session()
def benchmark(session):
    install_dev_deps(session, "5")
    session.run(
        "pytest",
        "--benchmark-only",
        "--benchmark-enable",
        "--benchmark-save=benchmark_results",
        "--benchmark-save-data",
    )
