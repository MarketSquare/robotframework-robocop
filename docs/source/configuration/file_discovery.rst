.. _file_discovery:

**************
File discovery
**************

Robocop by default search for any file with ``.robot`` and ``.resource`` extension in the current directory and its
subdirectories.

You can limit where Robocop looks for files by passing list of paths::

    robocop check tests/ bdd/ example.robot

While looking for the files, following options are taken into account:

- ``--exclude``, which allows to configure additional paths that will be ignored
- ``--default-exclude``, which defaults to ``.direnv, .eggs, .git, .svn, .hg, .nox, .tox, .venv, venv, dist``
- ``--include``, which allows to configure additional paths that should be included (for example ``*.txt`` files)
- ``--default-include``, which defaults to ``*.robot, *.resource``

Additionally Robocop finds and loads ``.gitignore`` files and exclude paths listed here. You can disable this behaviour
with ``--skip-gitignore`` option.

Paths passed from the cli are always included. For example following command::

    robocop format test.txt

Will format ``test.txt`` even if it doesn't match ``--default-include`` filter. You can disable this behaviour with
``--force-exclude`` which will also apply exclude filters on paths passed from the cli directly.
