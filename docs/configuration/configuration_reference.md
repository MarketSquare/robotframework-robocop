# Configuration reference

This page contains all available configuration options for Robocop.

## Common

#### ``include``

Use ``--include`` option to include additional files. By default, Robocop checks only files with
``.robot`` and ``.resource`` extension. Glob patterns are supported.

The following example will include all files ending with ``.task`` extension or named "special.file":

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --include *.task --include special.file
    robocop format --include *.task --include special.file
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    include = [
        "*.task",
        "special.file"
    ]
    ```

---

#### ``default include``

Use ``--default-include`` option to override default include patterns. By default, Robocop checks only files with
``.robot`` and ``.resource`` extension. Glob patterns are supported.

The following example will include all files ending with ``.robot`` extension (``.resource`` will be ignored since
we have overridden default include).

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --default-include *.robot
    robocop format --default-include *.robot
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    default-include = ["*.robot"]
    ```

---

#### ``exclude``

Use ``--exclude`` option to exclude additional files.
By default, Robocop ignores ``.direnv, .eggs, .git, .svn, .hg, .nox, .tox, .venv, venv, dist`` directories.
Glob patterns are supported.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --exclude tmp_dir
    robocop format --exclude tmp_dir
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    exclude = ["tmp_dir"]
    ```

---

#### ``default exclude``

Use ``--default-exclude`` option to override default exclude patterns. 
By default, Robocop ignores ``.direnv, .eggs, .git, .svn, .hg, .nox, .tox, .venv, venv, dist`` directories.
Glob patterns are supported.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --default-exclude .git
    robocop format --default-exclude .git
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    default-exclude = [".git"]
    ```

---

#### ``force exclude``

Use ``--force-exclude`` flag to force Robocop to process files even if they are passed from the cli.

Files specified directly on the command line are always included regardless of exclusion rules. By using this flag,
Robocop will respect the exclusion rules.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --force-exclude test.txt
    robocop format --force-exclude test.txt
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    force-exclude = true
    ```

---

#### ``skip gitignore``

Use ``--skip-gitignore`` flag to disable loading of ``.gitignore`` files.

Robocop will ignore all files listed in ``.gitignore`` files unless ``--skip-gitignore`` is used.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --skip-gitignore
    robocop format --skip-gitignore
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    skip-gitignore = true
    ```

---

#### ``language``

``--language`` / ``--lang`` option allows configuring language used for parsing source files.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --language fi --language pl
    robocop format --language fi --language pl
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    language = [
        "fi",
        "pl"
    ]
    ```

Custom language files are currently not supported.

---

### Configuration options

#### ``config``

Use ``--config`` to specify a configuration file. It disables automatic loading of configuration files found in the
directory tree.

```bash
robocop check --config robocop/config.toml
robocop format --config robocop/config.toml
```

---

#### ``configure``

``--configure`` / ``-c`` option allows configuring rules, formatters and linter reports. Exact parameters and their
types are described in their documentation. All parameters follow ``--configure name.param=value`` pattern for
providing values.

Typically, you can repeat it multiple times to configure multiple parameters.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure line-too-long.line_length=80 --configure sonarqube.output_path=robocop.json
    robocop format --configure NormalizeNewLines.section_lines=1 --configure NormalizeNewLines.keyword_lines=1
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "line-too-long.line_length=80",
        "sonarqube.output_path=robocop.json"
    ]
    [tool.robocop.format]
    configure = [
        "NormalizeNewLines.section_lines=1",
        "NormalizeNewLines.keyword_lines=1"
    ]
    ```

---

#### ``ignore git dir``

Use ``--ignore-git-dir`` flag to continue searching for configuration files even when encountering a ``.git`` directory.
By default, Robocop will stop searching for configuration files when encountering a ``.git`` directory.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --ignore-git-dir
    robocop format --ignore-git-dir
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    ignore-git-dir = true
    ```

---

#### ``ignore file config``

Ignore configuration files (``pyproject.toml``, ``.robocop.toml`` and ``robot.toml``) found in the directory tree
with ``--ignore-file-config`` flag.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --ignore-file-config
    robocop format --ignore-file-config
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    ignore-file-config = true
    ```

---

#### ``target version``

Use ``--target-version`` option to configure which Robot Framework version you want to target.
When configured, it will automatically disable all rules and formatters that require a more recent version of
Robot Framework.
It is useful if you have a legacy codebase you don't want to migrate yet, but the environment where you run Robocop
uses a more recent version of Robot Framework.

For example:

- if your codebase supports only Robot Framework 4.0, and your environment has 4.0, there is no need to configure anything
- if your codebase supports Robot Framework 4.0, and your environment has 5.0 or more recent, you need to configure
  a target version to 4

This option accepts a major version of Robot Framework (4, 5, .. ):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --target-version 5
    robocop format --target-version 5
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop]
    target-version = 5
    ```

---

## Linter

#### Selecting rules

#### ``select``

Use ``--select`` option to select rules to run. You can use rule id or rule name. Glob patterns are supported.
When this option is used, all other rules are disabled.

To only select and run ``missing-doc-keyword`` rule:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --select missing-doc-keyword
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    select = [
        "missing-doc-keyword"
    ]
    ```

You can select multiple rules:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --select unused-argument --select DUP01
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    select = [
        "unused-argument",
        "DUP01"
    ]
    ```

To only select and run rules with ``doc`` in their name:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --select *doc*
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    select = [
        "*doc*"
    ]
    ```

Use ``ALL`` keyword to select all rules (including rules disabled by default). You can combine it with ``--ignore`` 
option to select all rules except those you want to ignore:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --select ALL
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    select = [
        "ALL"
    ]
    ```

---

#### ``ignore``

Use ``--ignore`` option to ignore rules. You can use rule id or rule name. Glob patterns are supported.

To run all default rules except ``missing-doc-keyword`` rule:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --ignore missing-doc-keyword
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    ignore = [
        "missing-doc-keyword"
    ]
    ```

To ignore multiple rules:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --ignore missing-doc-keyword --ignore duplicated-test-case
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    ignore = [
        "missing-doc-keyword",
        "duplicated-test-case"
    ]
    ```

To ignore all rules with ``doc`` in their name:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --ignore *doc*
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    ignore = [
        "*doc*"
    ]
    ```

---

#### ``threshold``

Use ``--threshold`` / ``-t`` option to filter out rules that have lower severity than the threshold. Each rule has
assigned severity level (``info``, ``warning``, ``error``) which can be used to filter out rules. Shorthands can be
used:

- ``I`` for ``info``
- ``W`` for ``warning``
- ``E`` for ``error``

To filter our rules with severity ``info``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --threshold W
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    threshold = "W"
    ```

---

#### ``custom rules``

Read more about custom rules on the [Custom rules](../linter/custom_rules.md) page.

``--custom-rules`` option allows including custom rules.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --custom-rules my/own/rule.py --custom-rules custom_rules.py
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_rules = [
        "my/own/rule.py",
        "external_rules.py"
    ]
    ```

---

### Reports

#### ``reports``

Read more about reports on the [Reports](../linter/reports/reports.md) page.

Use ``--reports`` / ``-r`` option to configure which reports to generate.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports gitlab,file_stats
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "gitlab",
        "file_stats"
    ]
    ```

List all available reports with ``list reports`` command:

```bash
robocop list reports
```

---

#### ``persistent``

Use ``--persistent`` option to save Robocop reports in cache directory for later comparison.
Use it with a combination with ``--compare`` option to compare reports.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports file_stats --persistent
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    persistent = true
    reports = [
        "file_stats"
    ]
    ```

---

#### ``compare``

Use ``--compare`` option to compare Robocop reports with previous run. Requires ``--persistent`` option to be set
in previous run (to have results to compare with) with at least one report enabled.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports file_stats --compare
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    compare = true
    reports = [
        "file_stats"
    ]
    ```

For example, to compare reports, you can run:

```bash
roboocp check --reports rules_by_id --persistent
robocop check --reports rules_by_id --compare
```

You can combine both options and compare reports with previous run and save them in the cache directory:

```bash
roboocp check --reports rules_by_id --persistent --compare   # will save report and compare with previous run (if any)
robocop check --reports rules_by_id --persistent --compare   # will save report and compare with previous run
```

---

#### ``gitlab``

``--gitlab`` option is shorthand for ``--reports gitlab`` option. It will generate a GitLab compatible report.
See [the GitLab](../linter/reports/gitlab.md) page for more information.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --gitlab
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    gitlab = true
    ```

---

### Other

#### ``issue format``

``--issue-format`` option allows configuring output format of issues. 

It only affects ``simple`` output type. See [``print issues``](../linter/reports/print_issues.md) reporter to see all
possible output types and their configuration.

Available placeholders:

- ``{source}`` - source file name
- ``{source_abs}`` - absolute path to a source file
- ``{line}`` - line number
- ``{end_line}`` - end line number
- ``{col}`` - column number
- ``{end_col}`` - end column number
- ``{severity}`` - severity level (``info``, ``warning``, ``error``)
- ``{rule_id}`` - rule id
- ``{desc}`` - rule description
- ``{name}`` - rule name

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --issue-format "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    issue-format = "{source}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
    ```

Extended output configuration:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure print_issues.issue_format="{source}"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "print_issues.issue_format={source}"
    ]
    ```

---

#### ``exit zero``

Use ``--exit-zero`` option to exit with code ``0`` even if there are issues found.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --exit-zero
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    exit-zero = true
    ```

---

#### ``root``

Use ``--root`` to point to the project root directory. By default, Robocop finds it automatically based on existence of the ``.git``
directory. Root is used to find a default configuration file.

```bash
robocop check root /path/to/project/root
```

---

#### ``verbose``

Enable more verbose output with ``--verbose`` flag.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --verbose
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    verbose = true
    ```

---

## Formatter

### Selecting formatters

#### ``select``

Use ``--select`` option to select formatters to run. When this option is used, all other formatters are disabled.

???+ note

    If you want to only enable additional formatters and do not disable default ones, use
    ``--configure <formatter>.enabled=True`` configuration parameter instead.

To only select and run ``NormalizeSeparators`` formatter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select NormalizeSeparators
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "NormalizeSeparators"
    ]
    ```

You can select multiple formatters:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignVariablesSection --select OrderTags
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignVariablesSection",
        "OrderTags"
    ]
    ```

---

#### ``custom formatters``

Read more about custom formatters on the [Custom formatters](../formatter/custom_formatters.md) page.

``--custom-formatters`` option allows including custom formatters.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --custom-formatters my/own/Formatter.py --custom-formatters CustomFormatter.py
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    custom_formatters = [
        "my/own/Formatter.py",
        "CustomFormatter.py"
    ]
    ```

---

#### ``force order``

Use ``--force-order`` option to force order of the formatters (by order provided in the cli).

By default, all formatters run in the same order. Whether called with:

```bash
robocop format
```
   
or:

```bash
robocop format --select ReplaceRunKeywordIf --select SplitTooLongLine
```

or:

```bash
robocop format --select SplitTooLongLine --select ReplaceRunKeywordIf
```

It will format files according to internal order (in this example ``ReplaceRunKeywordIf`` is before
``SplitTooLongLine``). External formatters are used last. To see order of the formatters run
``robocop list formatters``.

If you want to format files using a different order, you need to run formatters separately:

```bash
robocop format --select SplitTooLongLine
robocop format --select ReplaceRunKeywordIf
```

This behaviour can be changed by using ``--force-order`` flag:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --force-order --select SplitTooLongLine --select ReplaceRunKeywordIf
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    force-order = true
    select = [
        "SplitTooLongLine",
        "ReplaceRunKeywordIf"
    ]
    ```

---

### Work modes

---

#### ``overwrite``

By default, Robocop overwrites the file with formatted code. You can enable/disable this behaviour with ``--overwrite``
/ ``--no-overwrite`` flag.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --no-overwrite
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    overwrite = false
    ```

---

#### ``diff``

Show difference after formatting the file with the ``--diff`` option.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --diff
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    diff = true
    ```

---

#### ``color``

Use ``--color`` / ``--no-color`` option to enable/disable color output. By default, Robocop uses color output.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --no-color
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    color = false
    ```

---

#### ``check``

Check is a special mode used to check if the file is formatted correctly. If the file is not formatted correctly,
Robocop will return exit code ``1``. The files are not overwritten (turn back overwriting with ``--overwrite`` flag).

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --check
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    check = true
    ```

---

#### ``reruns``

Rerun formatter with the given number of times using ``--reruns`` option. Default value is ``0`` (do not rerun).

If the file was modified during the last run, the formatter will be rerun until the file is not modified.

This option is useful when you have a formatter that changes the formatting of the previous formatter. For example,
if you align the code first, and then you add new code in another formatter, you may want to rerun the formatter so
 the new code is aligned.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --reruns 3
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    reruns = 3
    ```
Note that if you enable it, it can double the execution time of Robocop.

---

### Formatting settings

#### ``space count``

Use ``--space-count`` to configure number of spaces between cells (default ``4``). Most of the formatters use this value
to align code.

??? info "Spacing attributes names"

    ```robotframework
    *** Keywords ***
    Custom Keyword
        Keyword Call
        (1)...    (2)${arg}
        (1)...    (2)${arg2}
        (1)Log    (3)${value}
    ```

    1. Indent
    2. Continuation indent
    3. Space count

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --space-count 2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    space-count = 2
    ```

---

#### ``indent``

Use ``--indent`` to configure indentation of code. Default value is the same as ``space count`` option (``4``).

??? info "Spacing attributes names"

    ```robotframework
    *** Keywords ***
    Custom Keyword
        Keyword Call
        (1)...    (2)${arg}
        (1)...    (2)${arg2}
        (1)Log    (3)${value}
    ```

    1. Indent
    2. Continuation indent
    3. Space count

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --indent 2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    indent = 2
    ```

---

#### ``continuation indent``

Use ``--continuation-indent`` to configure indentation of continuation lines. Default value is the same as
``space count`` option (``4``).

??? info "Spacing attributes names"

    ```robotframework
    *** Keywords ***
    Custom Keyword
        Keyword Call
        (1)...    (2)${arg}
        (1)...    (2)${arg2}
        (1)Log    (3)${value}
    ```

    1. Indent
    2. Continuation indent
    3. Space count

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --continuation-indent 2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    continuation-indent = 2
    ```

---

#### ``line length``

Number of characters per line. This value is used by formatters that split long lines into multiple lines to determine
where to split the line. Use ``--line-length`` option to configure line length (default ``120``).

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --line-length 140
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    line-length = 140
    ```

---

#### ``separator``

Use ``--separator`` option to configure separator between cells. Default value is ``space``:

- ``space``: use ``--space-count`` spaces to separate tokens
- ``tab``: use single tabulation to separate tokens

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --separator space
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    separator = "space"
    ```

---

#### ``line ending``

When working on multiple platforms, the file can contain different line endings (``CRLF``, ``LF``). By default,
Robocop will replace all line endings with system native line ending. It may be problematic if you're using
different platforms. You can force specific line ending or autodetect line ending used in the file and use it by
configuring ``--line-ending`` option:

- native:  use operating system's native line endings (default)
- windows: use Windows line endings (CRLF)
- unix:    use Unix line endings (LF)
- auto:    maintain existing line endings (uses what's used in the first line of the file)

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --line-ending unix
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    line-ending = "unix"
    ```

---

#### ``start line``

Use ``--start-line`` option to configure line number where formatter should start. If ``--end-line`` is not provided,
format text only at ```--start-line``.

This option is useful when you want to format only a part of the file, it is typically useful with the automatic
tooling. We don't recommend using this option with the manual execution.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --start-line 10
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    start-line = 10
    ```

---

#### ``end line``

Use ``--end-line`` option to configure line number where formatter should end. Use it only with a combination with
``--start-line``.

This option is useful when you want to format only a part of the file, it is typically useful with the automatic
tooling. We don't recommend using this option with the manual execution.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --start-line 10 --end-line 20
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    start-line = 10
    end-line = 20
    ```

---

### Skip formatting

#### ``skip``

Use ``--skip`` option to skip formatting code of a given type.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip documentation
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip = ["documentation"]
    ```

See [skip option](../formatter/skip_formatting.md#skip-option) for more details.

---

#### ``skip sections``

Use ``--skip-sections`` option to skip formatting code of a given section.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip-sections=keywords,testcases
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip-sections = [
        "keywords",
        "testcases"
    ]
    ```

See [skip sections](../formatter/skip_formatting.md#skip-sections) for more details.

---

#### ``skip keyword call``

Use ``--skip-keyword-call`` option to skip formatting code of a given keyword call.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip-keyword-call Name --skip-keyword-call othername
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip-keyword-call = [
        "Name",
        "othername"
    ]
    ```

See [skip keyword call](../formatter/skip_formatting.md#skip-keyword-call) for more details.

---

#### ``skip keyword call pattern``

Use ``--skip-keyword-call-pattern`` option to skip formatting code of a given keyword call that matches a configured
pattern.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip-keyword-call-pattern ^Second --skip-keyword-call-pattern (i?)contains\s?words
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip-keyword-call-pattern = [
        "^Second",
        "(i?)contains\s?words"
    ]
    ```

See [skip keyword call pattern](../formatter/skip_formatting.md#skip-the-keyword-call-pattern) for more details.
