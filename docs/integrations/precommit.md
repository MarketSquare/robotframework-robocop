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
```

Place this file in the root of your project. Follow instructions on the [pre-commit](https://pre-commit.com) website
to install it.

It will run both linter and formatter on your modified files when trying to commit changes. If any linter issue is
found or a file is modified, it will stop the commit.

If you select [project level rules](../linter/linter.md#project-checks), the ``robocop`` hook parses the whole project
on every run, which can be noticeably slower. Add ``--no-project`` to the hook arguments to skip it:

```yaml
        - id: robocop
          args: [--force-exclude, --no-project]
```

``rev`` is the version of the Robocop, prefixed with ``v``. It matches the release tag created in our repository on each
release.
