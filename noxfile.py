"""
Generate docs with:

> uv run nox -s docs
"""

import os

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]

ROBOT_VERSIONS = ["robotframework==4.*", "robotframework==5.*", "robotframework==6.*", "robotframework==7.*"]
ROBOCOP_VERSIONS = (
    [*[non_empty for non_empty in os.environ["ROBOCOP_VERSIONS"].split(",") if non_empty], "local"]
    if os.environ.get("ROBOCOP_VERSIONS")
    else ["v7.1.0", "local"]
)


@nox.session(python=PYTHON_VERSIONS)  # , reuse_venv=False
@nox.parametrize("robot_ver", ROBOT_VERSIONS)
def tests(session: nox.Session, robot_ver: str) -> None:
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


def install_doc_deps(session: nox.Session, robot_version: str) -> None:
    session.install(f"robotframework=={robot_version}")
    session.run(*["uv", "sync", "--frozen", "--group", "doc"])


@nox.session()
def docs(session: nox.Session) -> None:
    install_doc_deps(session, "7.2.2")
    command = ["mkdocs", "build", "--clean", "--verbose", "--config-file", "mkdocs.yml"]
    session.run(*command)


@nox.session(python=PYTHON_VERSIONS[-2])
@nox.parametrize("robocop_version", ROBOCOP_VERSIONS)
def performance(session: nox.Session, robocop_version: str) -> None:
    """
    Generate performance reports.

    Used by the GitHub Workflow: ``.github/workflows/release_check.yml``

    ROBOCOP_VERSIONS is created based on the environment variable in the workflow (set to latest 4 released tags) and
    "latest" which means local installation. The goal is to execute performance tests in the isolated environment with
    a selected past/current Robocop version for comparison.

    The reports are designed in a way that specific results do not matter, but change between a version does. We are
    re-executing the tests for the past version to get the baseline benchmark for the current version.
    """
    robocop_version = robocop_version.removeprefix("v")
    if not robocop_version:
        return
    if robocop_version == "local":
        session.run_install(
            "uv",
            "sync",
            f"--python={session.virtualenv.location}",
            env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        )
    else:
        session.run(
            "uv",
            "pip",
            "install",
            f"robotframework-robocop=={robocop_version}",
            f"--python={session.virtualenv.location}",
            env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        )
    session.run("python", "-m", "tests.performance.generate_reports", robocop_version, external=True, silent=False)
