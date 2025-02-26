---- Document under rework -----

Documentation
=============

Robocop uses both dynamically and statically loaded documentation. For documentation backend we are using Sphinx with
furo theme. Documentation source files are stored in ``docs/source``.

After merging the changes, documentation is rebuilt and deployed at https://robocop.readthedocs.io/ . It is however
advised to build documentation locally to check it.

If you are adding or updating new features you may need to update relevant sections in the documentation. For example
if you're changing how external rules works, you may need to update ``docs/source/external_rules.rst`` document.

If you are adding or updating formatter, you need to add or modify file at ``docs/source/formatters/<formatter_name>rst``
(more on this in <> section). # TODO

If you are adding or updating rule, you need to update rule docstring and check how the rule documentation generates
at https://robocop.readthedocs.io/en/stable/rules_list.html . Check <> to see how to add or update existing rules. # TODO

Build documentation locally
----------------------------

If you have Robocop development environment ready (with uv installed), run:

```
    uv run nox -s docs
```

Documentation will build at ``docs/_build``. Open ``docs/_build/index.thml`` to see starting page.
