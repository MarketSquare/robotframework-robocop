"""
Generate docs with:

> uv run nox -s docs
"""

import nox

nox.options.default_venv_backend = "uv"


def install_doc_deps(session, robot_version):
    session.install(f"robotframework=={robot_version}")
    session.run("uv", "sync", "--group", "doc")


@nox.session()
def docs(session):
    install_doc_deps(session, "7.2.2")
    # session.run("sphinx-build", "-a", "-E", "-b", "html", "docs", "docs/_build/")
    command = "sphinx-build -a -E --verbose -b html docs/source docs/_build/".split()
    session.run(*command)
