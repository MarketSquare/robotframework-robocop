.. _including-rules:

Including and excluding rules
==============================

You can include or exclude particular rules using rule name or id.
Rules are matched in similar way how Robot Framework ``include`` / ``exclude`` arguments.

Described examples::

    robocop --include missing-doc-keyword test.robot

All rules will be ignored except ``missing-doc-keyword`` rule::

    robocop --exclude missing-doc-keyword test.robot

Only ``missing-doc-keyword`` rule will be ignored.

Robocop supports glob patterns::

    robocop --include *doc* test.robot

All rules will be ignored except those with *doc* in its name (like ``missing-doc-keyword``, ``too-long-doc`` etc).

You can provide list of rules in comma-separated format or repeat the argument with value::

    robocop --include rule1,rule2,rule3 --exclude rule2  --exclude rule1 test.robot

You can also use short names of options::

    robocop -i rule1 -e rule2 test.robot
