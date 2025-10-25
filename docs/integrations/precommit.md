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

``rev`` is the version of the Robocop, prefixed with ``v``. It matches the release tag created in our repository on each
release.
