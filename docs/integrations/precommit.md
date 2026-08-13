# pre-commit

To use Robocop as a [pre-commit](https://pre-commit.com) hook, you need the following ``.pre-commit-config.yaml`` file:

```yaml
repos:
    - repo: https://github.com/MarketSquare/robotframework-robocop
      # Robocop version.
      rev: v{{ robocop_version() }}
      hooks:
        # Run the linter.
        - id: robocop
        # Run the formatter.
        - id: robocop-format
        # Run the project checker.
        - id: robocop-check-project
```

Place this file in the root of your project. Follow instructions on the [pre-commit](https://pre-commit.com) website
to install it.

It will run both linter and formatter on your modified files when trying to commit changes. If any linter issue is
found or a file is modified, it will stop the commit.

The ``robocop-check-project`` hook runs the project checker, which analyzes rules that require the whole project
context. It is filtered to only run on ``.robot`` and ``.resource`` files by default. If you want it to trigger on
other files as well, override the ``files`` option in your ``.pre-commit-config.yaml``.

``rev`` is the version of the Robocop, prefixed with ``v``. It matches the release tag created in our repository on each
release.
