# User Guide

## Requirements

Python 3.9+ and Robot Framework 4+.

## Installation

You can install Robocop by running:

```bash
pip install robotframework-robocop
```

## Robocop linter

Robocop can scan Robot Framework files and report any potential issues.

Use ``check`` command to run the linter:

```bash
robocop check                  # lint Robot files in the current directory and subdirectories
robocop check -h               # list all available options
robocop check path             # lint Robot files in the given path
```

Read more about linting on the [Linting](../linter/linter.md) page.

## Robocop formatter

Robocop can format Robot Framework files to ensure a consistent code style.

Use ``format`` command to run the formatter:

```bash
robocop format                 # format Robot files in the current directory and subdirectories
robocop format -h              # list all available options
robocop format path            # format Robot files in the given path
robocop format --diff          # format files and show difference after formatting
robocop format --no-overwrite  # format files but don't overwrite them (combine with --diff for dryrun)
```

Read more about formatting on the [Formatting](../formatter/formatter.md) page.

### File discovery

Robocop by default searches for any file with ``.robot`` and ``.resource`` extension in the current directory and its
subdirectories.

You can limit where Robocop looks for files by passing a list of paths:

```bash
robocop check tests/ bdd/ example.robot
```

While looking for the files, the following options are taken into account:

- [``--exclude``](../configuration/configuration_reference.md#exclude), which allows configuring additional paths that
  will be ignored
- [``--default-exclude``](../configuration/configuration_reference.md#default-exclude), which defaults to
  ``.direnv, .eggs, .git, .svn, .hg, .nox, .tox, .venv, venv, dist``
- [``--include``](../configuration/configuration_reference.md#include), which allows configuring additional paths that
  should be included (for example ``*.txt`` files)
- [``--default-include``](../configuration/configuration_reference.md#default-include), which defaults to
  ``*.robot, *.resource``

Additionally, Robocop finds and loads ``.gitignore`` files and exclude paths listed here. You can disable this behaviour
with [``--skip-gitignore``](../configuration/configuration_reference.md#skip-gitignore) option.

Paths passed from the cli are always included. For example, the following commands:

```bash
robocop check test.txt
robocop format test.txt
```

Will process ``test.txt`` file even if it doesn't match ``--default-include`` filter. You can disable this behaviour with
[``--force-exclude``](../configuration/configuration_reference.md#force-exclude) which will also apply exclude filters
on paths passed from the cli directly.

## Shell autocompletion

It is possible to use shell autocompletion by installing it for the current shell:

```bash
robocop --install-completion
```

## List available rules, reports and formatters

To list all available rules, reports and formatters use ``list`` command with the name of the category:

```bash
robocop list rules
robocop list reports
robocop list formatters
```

Combine it with ``--help`` to get more information on additional filter options.

## See documentation for the specific rule, report or formatter

Print rule, report or formatter documentation with ``docs`` command:

```bash
robocop docs <name>
```

Examples:

```bash
# see rules documentation
robocop docs invalid-argument
robocop docs VAR02
# see formatter documentation
robocop docs NormalizeNewLines
# see report documentation
robocop docs sonarqube
```

## Values

Original *RoboCop* - a fictional cybernetic police officer - was the following three prime directives 
which also drive the progress of Robocop linter:

First Directive: **Serve the public trust**

Which lies behind the creation of the project - to **serve** developers and testers as a tool to build applications they can **trust**.

Second Directive: **Protect the innocent**

**The innocent** testers and developers have no intention of producing ugly code, but sometimes, you know, it just happens,
so Robocop is there to **protect** them.

Third Directive: **Uphold the law**

Following the coding guidelines established in the project are something crucial to keep the code clean,
readable and understandable by others, and Robocop can help to **uphold the law**.
