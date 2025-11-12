# Skip formatting

It is possible to skip formatting on code of a given type. Skip options apply to all instances of the
given code. For example, it is possible to skip formatting on all documentation. If you want to disable formatting
on specific lines, see [disablers](../configuration/disablers.md).

To see what types are possible to skip, see ``Skip formatting`` sections in each formatter documentation.

## Skip option

Option that allows skipping a configured type of the code. Supported types:

* --skip documentation
* --skip return-values
* --skip settings
* --skip arguments
* --skip setup
* --skip teardown
* --skip timeout
* --skip template
* --skip return
* --skip tags
* --skip comments
* --skip block-comments

Example usage:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip documentation
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip = ["documentation"]
    ```

To configure it on the formatter level, or overwrite global setting use ``skip_<name>=True/False`` syntax:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --skip documentation --configure NormalizeSeparators.skip_documentation=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    skip = ["documentation"]
    configure = [
        "NormalizeSeparators.skip_documentation=False"
    ]
    ```

## Skip keyword call

Comma-separated list of keyword call names that should not be formatted. Names will be
normalised before search (spaces and underscores removed, lowercase).

With this configuration:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.skip_keyword_call=ExecuteJavascript,catenate
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.skip_keyword_call=ExecuteJavascript,catenate"
    ]
    ```

All instances of ``Execute Javascript`` and ``Catenate`` keywords will not be formatted.

It is possible to use a global option to skip formatting for every formatter that supports it:

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

## Skip the keyword call pattern

Comma-separated list of keyword call name patterns that should not be formatted. The keyword names are not normalised.
If you're using a different case for the same keyword ("Keyword" and "keyword") or using both spaces and underscores, it
is recommended to use proper regex flags to match it properly.

With this configuration:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignKeywordsSection -c AlignKeywordsSection.skip_keyword_call_pattern=^First,(i?)contains\s?words
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignKeywordsSection"
    ]
    configure = [
        "AlignKeywordsSection.skip_keyword_call_pattern=^First,(i?)contains\s?words"
    ]
    ```

All instances of keywords that start with "First" or contain "contains words" (case-insensitive, space optional) will
not be formatted.

> Note that a list is comma-separated - it is currently not possible to provide regex with ``,``.

It is possible to use a global option to skip formatting for every formatter that supports it:

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

## Skip sections

Option that disables formatting of the selected sections. Example usage:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c NormalizeSeparators.skip_sections=variables
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeSeparators.skip_sections=variables"
    ]
    ```

It is possible to use a global option to skip formatting for every formatter that supports it:

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

Section names can be provided using a comma-separated list: ``settings,variables,testcases,keywords,comments``.
