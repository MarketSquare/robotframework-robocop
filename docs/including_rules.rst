.. _including-rules:

Including  and excluding rules
==============================

You can include or exclude particular rules using rule name or id.
Rules are matched in similar way how Robot Framework include/exclude arguments.

Described examples::

    robocop --include missing-keyword-doc test.robot

All rules will be ignored except ``missing-keyword-doc`` rule::

    robocop --exclude missing-keyword-doc test.robot


Only ``missing-keyword-doc`` rule will be ignored.

Robocop supports glob patterns::

    robocop --include *doc* test.robot

All rules will be ignored except those with doc in its name (like ``missing-doc-keyword``, ``too-long-doc`` etc).

You can provide list of rules in comma separated format or repeat the argument::

    robocop --include rule1,rule2,rule3 --exclude rule2  --exclude rule1 test.robot

You can also use short names of options::

    robocop -i rule1 -e rule2 test.robot

Ignore rule from source code
----------------------------

Rules can be also disabled directly from Robot Framework code. It is similar to how # noqa comment works for
most linters. Examples::

    *** Test Cases ***
    Some Test  # robocop: disable=missing-doc-testcase
        Keyword 1
        Keyword 2
        Keyword 3

    *** Keywords ***
    # robocop: disable
    Keyword 1
        Log  1

    Keyword 2
        Log  2

    # robocop: enable

In this example we are disabling missing-doc-testcase rule in 2nd line of file. Also we are disabling all rules in
keywords section. It is possible to ignore whole file if you start file with ``# robocop: disable`` and won't provide
``# robocop: enable`` before end of file.