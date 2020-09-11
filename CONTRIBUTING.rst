Contribution guidelines
=======================

These guidelines instruct how to submit issues and contribute code or
documentation to the `Robocop project
<https://github.com/bhirsz/robotframework-robocop>`_.
Another way to contribute includes participating in discussion and answering
questions on our `Slack workspace <https://rf-robocop.slack.com>`_. We have
some dedicated channels for all different types of topics. One of the best
ways to support is to help us **grow** so don't hesitate and spread the word
about Robocop!

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
<https://github.com/bhirsz/robotframework-robocop/issues>`_.

Before submitting a new issue, it is always a good idea to check if the
same bug or enhancement is already reported. If it is, please add your comments
to the existing issue instead of creating a new one.

Reporting bugs
~~~~~~~~~~~~~~

::

    They'll fix you. They fix everything. — Robocop

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

    Stay out of trouble. – Robocop

General guidelines
''''''''''''''''''

Robocop uses the general Python code conventions defined in `PEP-8
<https://www.python.org/dev/peps/pep-0008/>`_.
An important guideline is that the code should be clear enough that
comments are generally not needed.

All code, including test code, must be compatible with all supported Python
interpreters and versions. Most importantly this means that the code must
support Python 3.6+ and Robot Framework 3.2.1+.

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

User manual
''''''''''

Robocop's main features are explained in the `README
<https://github.com/bhirsz/robotframework-robocop/blob/master/README.rst>`_.
The whole documentation is available `here <https://robocop.readthedocs.io/>`_.


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

Executing changed code
''''''''''''''''''''''

If you need to check if your code is working fine, feel free to add Robot
Framework files to ``tests/test_data`` directory and run robocop against this
file to test your changes. These files will be used for acceptance tests
that will be created soon.


Unit tests
''''''''''

Unit tests are great for testing internal logic and should be added when
appropriate. They are located in ```tests/utest`` directory. To run them
you need to have installed `pytest <https://docs.pytest.org/en/stable/>`_.
Run the tests by executing command:

::

    pytest .

Pytest will automatically discover all the tests, run them and display
results. Make sure that tests do not fail.


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

::

    Thank you for your cooperation. Good night. — Robocop
