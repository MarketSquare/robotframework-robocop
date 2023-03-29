Contribution guidelines
=======================

These guidelines instruct how to submit issues and contribute code or
documentation to the `Robocop project
<https://github.com/MarketSquare/robotframework-robocop>`_.
Another way to contribute includes participating in discussion and answering
questions on our Slack channel `#robocop-linter
<https://robotframework.slack.com/archives/C01AWSNKC2H>`_ located in
`Robot Framework workspace <https://robotframework.slack.com/>`_. We have some
dedicated channels for all different types of topics. One of the best ways to
support is to help us **grow** so don't hesitate and spread the word about
Robocop!

These guidelines expect readers to have a basic knowledge about open source
as well as why and how to contribute to open source projects. If you are
totally new to these topics, it may be a good idea to look at the generic
`Open Source Guides <https://opensource.guide/>`_ first.

.. contents::
   :depth: 2
   :local:

Submitting issues
-----------------

Bugs and enhancements are tracked in the `issue tracker
<https://github.com/MarketSquare/robotframework-robocop/issues>`_.

Before submitting a new issue, it is always a good idea to check if the
same bug or enhancement is already reported. If it is, please add your comments
to the existing issue instead of creating a new one.

Reporting bugs
~~~~~~~~~~~~~~

::

    They'll fix you. They fix everything. - Robocop

The preferred way to report a bug is to create an issue using
**Bug report** template and fill in the blanks:

1. Explanation of a bug

2. Steps to reproduce the problem

3. Output with error message

4. Expected behavior

5. Version information (Robocop version, Python version, operating system etc.)

Notice that all information in the issue tracker is public. Do not include
any confidential information there.

Enhancement requests
~~~~~~~~~~~~~~~~~~~~

To suggest an idea for the project please create an issue using
**Feature request** template. Try to write clear and concise description of
why this should be useful and what needs to be done to accomplish the goal.

Code contributions
------------------

If you have fixed a bug or implemented an enhancement, you can contribute
your changes via GitHub's pull requests. This is not restricted to code,
on the contrary, fixes and enhancements to documentation_ and tests_ alone
are also very valuable.

Pull requests
~~~~~~~~~~~~~

On GitHub pull requests are the main mechanism to contribute code. They
are easy to use both for the contributor and for the person accepting
the contribution, and with more complex contributions it is easy also
for others to join the discussion. Preconditions for creating pull
requests are having a `GitHub account <https://github.com/>`_,
installing `Git <https://git-scm.com>`_ and forking the
`Robocop project`_.

GitHub has good articles explaining how to
`set up Git <https://help.github.com/articles/set-up-git/>`_,
`fork a repository <https://help.github.com/articles/fork-a-repo/>`_ and
`use pull requests <https://help.github.com/articles/using-pull-requests>`_
and we do not go through them in more detail. We do, however, recommend to
create dedicated topic branches for pull requests instead of creating
them based on the master branch. This is especially important if you plan to
work on multiple pull requests at the same time.

Coding conventions
~~~~~~~~~~~~~~~~~~

::

    Stay out of trouble. - Robocop

General guidelines
''''''''''''''''''

Robocop uses the general Python code conventions defined in `PEP-8
<https://www.python.org/dev/peps/pep-0008/>`_.
An important guideline is that the code should be clear enough that
comments are generally not needed.

All code, including test code, must be compatible with all supported Python
interpreters and versions. Most importantly this means that the code must
support Python 3.7+ and Robot Framework 3.2.2+.

To ensure high quality of the code we use `pylama
<https://github.com/klen/pylama>`_ static code analysis tool to check
against common errors and mistakes. The tool needs to be run with
configuration file ``pylama.ini`` located in the root of the repository.
Execute the command before creating a pull request (you must have pylama
installed):

::

    pylama -o pylama.ini

Docstrings
''''''''''

Docstrings should be added to public APIs, but they are not generally needed in
internal code. When docstrings are added, they should follow `PEP-257
<https://www.python.org/dev/peps/pep-0257/>`_.

Documentation
~~~~~~~~~~~~~

With new features adequate documentation is as important as the actual
functionality. Different documentation is needed depending on the issue
but most of it is located inside ``docs`` directory. The files are usually
written using `reStructuredText format
<https://www.writethedocs.org/guide/writing/reStructuredText/>`_ (.rst).

To generate our documentation use ``nox`` tool that will create environment with required dependencies and generate
the documentation. Documentation will be available under ``docs/_build/index.html`` path::

    nox -s docs

User manual
'''''''''''

Robocop's main features are explained in the `README
<https://github.com/MarketSquare/robotframework-robocop/blob/master/README.md>`_.
The whole documentation is available `here <https://robocop.readthedocs.io/>`_.

Pre-commit checks
~~~~~~~~~~~~~~~~~~~~
Every change is required to pass pre-commit checks. To install pre-commit tool run::

    pip install pre-commit

Then install the pre-commits for this repository run in the root::

    pre-commit install

Now all commits will trigger pre-commit script that will scan & format your code.

Tests
~~~~~

When submitting a pull request with a new feature or a fix, you should
always include tests for your changes. These tests prove that your changes
work, help prevent bugs in the future, and help document what your changes
do. Depending on the change, you may need acceptance tests, unit tests
or both.

Make sure to run all of the tests before submitting a pull request to be sure
that your changes do not break anything. Pull requests are also automatically
tested on continuous integration.

Most of our tests use pytest. To use it install Robocop with ``dev`` profile::

    pip install robotframework-robocop[dev]

To run pytest tests navigate to directory with test files and run::

    pytest .

Pytest will automatically discover all the tests, run them and display
results. Make sure that tests do not fail.

Nox
''''''''
Robocop contains `nox <https://nox.thea.codes/en/stable/>`_ file for running the tests on all supported
major Robot Framework versions and generating the coverage or docs. The nox tool will create the virtual environment and
install required dependencies for you.

Follow installation instruction from the ``nox`` documentation page. To execute Robocop tests run::

    nox

Run the following command to see all possible sessions (acting as environments or targets)::

    nox --list

You can select only one session per run. For example, to only run tests for ``Python==3.10`` and ``Robot Framework==3.*``::

    nox --session "unit-3.10(robot_version='3')"

Unit tests
''''''''''

Unit tests are great for testing internal logic and should be added when
appropriate. They are located in ``tests/utest`` directory.

Acceptance tests
''''''''''''''''

Acceptance tests check if Robocop rules report issues in test data files.

They are located in ``tests/atest/rules/{rules_category}`` directories.
Each rule has its subdirectory with the name of the rule. Hyphens in the
name are replaced by underscores. For example, ``rule-name`` from ``comments``
category rule should have ``tests/atest/rules/comments/rule_name`` directory.
Inside each directory there should be an empty ``__init__.py`` file, ``test_rule.py``
file containing pytest tests, test data and expected data used by the tests.

Acceptance tests should use ``tests.atest.utils.RuleAcceptance`` class that
contains helper methods and assertions for the tests purpose.
Example of a simple test::

    from tests.atest.utils import RuleAcceptance


    class TestRuleAcceptance(RuleAcceptance):
        def test_rule(self):
            self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

In this example we're invoking Robocop on ``test.robot`` file inside the same directory and
we're comparing reported issues with the content of the ``expected_output.txt`` file.

Example of the expected file::

    test.robot:8:1 [E] 0803 Multiple variables with name '${V AR}' in Variables section (first occurrence in line 6). Note that Robot Framework is case-insensitive

Issues are reported using following format: ``{source}:{line}:{col} [{severity}] {rule_id} {desc}``.
If your test data file is inside subdirectory, the path to file should use ``${/}`` as path separator::

    suite_dir{/}__init__.robot:4:1 [W] 0806 Duplicated metadata 'some text' (first occurrence in line 2)

If the rule behaves differently depending on the Robot Framework version, or it is enabled only for
specific version, it is possible to set target version of the tests using version specifiers::

    from tests.atest.utils import RuleAcceptance


    class TestRule(RuleAcceptance):
        def test_rule(self):
            self.check_rule(expected_file="expected_output.txt", target_version=">=5.0")

        def test_rule_rf3(self):
            self.check_rule(expected_file="expected_output_rf4.txt", target_version="==4.1.3")

        def test_rule_rf4(self):
            self.check_rule(expected_file="expected_output_rf3.txt", target_version="==3.2.2")

You can provide custom configuration for the rule using ``config`` argument. It accepts either string or list::

    from tests.atest.utils import RuleAcceptance


    class TestRuleAcceptance(RuleAcceptance):
        def test_configure_pattern(self):
            self.check_rule(
                config="-c not-allowed-char-in-filename:pattern:\.(?!bar)",
                src_files=["allowed_suite_foo.bar.robot", "suite.withdot"],
                expected_file="expected_output_configured.txt",
            )

Set ``expected_file`` to ``None`` if you expect the rule to not raise any issues during run::

    self.check_rule(src_files=["golden.robot"], expected_file=None)

E2E tests
'''''''''

Simple E2E tests are also included in repository in ``tests/e2e`` directory.
They are being run automatically along with unit tests when ``pytest`` is
executed.

Coverage
''''''''

Tests coverage cannot drop under 90%. If your changes affect the coverage
significantly, please write new tests to satisfy the expected threshold,
otherwise continuous integration will not permit to merge the changes.

To calculate coverage locally run::

    coverage run -m pytest

and then::

    coverage html

You can also use ``nox`` tool::

    nox -s coverage

HTML files will be generated - navigate to ``htmlcov`` directory and open ``index.html`` file.

::

    Thank you for your cooperation. Good night. - Robocop
