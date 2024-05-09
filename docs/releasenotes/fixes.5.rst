Relative paths in argument files (#1071)
-----------------------------------------

Relative paths in argument files will be now resolved correctly. For example, using following command::

    robocop -A tests/args.txt

And tests/args.txt file::

    --ext-rules rules/robocop_rules.py

``--ext-rules rules/robocop_rules.py`` will be resolved to ``--ext-rules tests/rules/robocop_rules.py``. This
behaviour already worked for toml configuration files and wasn't working correctly for argument files.
