# AlignBDDStatements

Align BDD statements in the test case body.

{{ enable_hint("AlignBDDStatements") }}

Keyword calls prefixed with the BDD reserved keywords (``Given``, ``When``, ``And``, ``But`` and ``Then``) are
indented so the keyword names following the prefixes are aligned in a single column:

=== "Before"

    ```robotframework
    *** Test Cases ***
    There can be only one
        Given there are 3 ninjas
        And there are more than one ninja alive
        When 2 ninjas meet, they will fight
        Then one ninja dies (but not me)
        And there is one ninja less alive
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    There can be only one
        Given there are 3 ninjas
          And there are more than one ninja alive
         When 2 ninjas meet, they will fight
         Then one ninja dies (but not me)
          And there is one ninja less alive
    ```

The width of the column is calculated separately for every test case using the longest BDD prefix used in its body.
Nested blocks (such as ``IF`` or ``FOR``) are aligned separately, using their own indentation as a base.
Statements that do not start with the BDD prefix, keyword calls with the assignment and keywords from the
``*** Keywords ***`` section are not formatted.

BDD prefixes translated to other languages are recognized if the language is configured with the
[``--language``](../../configuration/configuration_reference.md#language) option or with the language header.

## Indentation

The shortest BDD statement keeps the normal indentation. It can be configured with the global
[``--indent``](../../configuration/configuration_reference.md#indent) option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignBDDStatements --indent 2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignBDDStatements"
    ]
    indent = 2
    ```

=== "Before"

    ```robotframework
    *** Test Cases ***
    There can be only one
        Given there are 3 ninjas
        And there are more than one ninja alive
        When 2 ninjas meet, they will fight
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    There can be only one
      Given there are 3 ninjas
        And there are more than one ninja alive
       When 2 ninjas meet, they will fight
    ```
