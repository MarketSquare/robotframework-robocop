"""
Generate docs with:

> uv run nox -s docs
"""

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]

ROBOT_VERSIONS = ["robotframework==4.*", "robotframework==5.*", "robotframework==6.*", "robotframework==7.*"]


@nox.session(python=PYTHON_VERSIONS)  # , reuse_venv=False
@nox.parametrize("robot_ver", ROBOT_VERSIONS)
def tests(session, robot_ver):
    """
    Run tests with a given Python version and dependency version.

    To run single session use the following format:

    > nox -s "tests-3.9(robot_ver='robotframework==4.*')"
    """
    session.run_install(
        "uv",
        "sync",
        "--group=dev",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run(
        "uv",
        "add",
        robot_ver,
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("robot", "--version", success_codes=[0, 251])
    session.run("pytest", "-v")


def install_doc_deps(session, robot_version):
    session.install(f"robotframework=={robot_version}")
    session.run(*"uv sync --frozen --group doc".split())


@nox.session()
def docs(session):
    install_doc_deps(session, "7.2.2")
    # session.run("sphinx-build", "-a", "-E", "-b", "html", "docs", "docs/_build/")
    command = "sphinx-build -a -E --verbose -b html docs/source docs/_build/".split()
    session.run(*command)
