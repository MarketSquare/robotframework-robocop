# RenameVariables

Rename and normalize variable names.

{{ enable_hint("RenameVariables") }}

Variable names in the Settings, Variables, Test Cases and Keywords section are renamed. Variables in arguments are
also affected.

The following conventions are applied:

- the variable case depends on the variable scope (lowercase for local variables and uppercase for non-local variables)
- leading and trailing whitespace is stripped
- more than 2 consecutive whitespace in name is replaced by 1
- whitespace is replaced by _
- camelCase is converted to snake_case

Conventions can be configured or switched off using parameters.

=== "Before"

    ```robotframework
    *** Settings ***
    Suite Setup    ${keyword}

    *** Variables ***
    ${global}    String with {other global}

    *** Test Cases ***
    Test
        ${local}    Set Variable    variable
        Log    ${local}
        Log    ${global}
        Log    ${local['item']}

    *** Keywords ***
    Keyword
        [Arguments]    ${ARG}
        Log    ${arg}

    Keyword With ${EMBEDDED}
        Log    ${emb   eded}
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Suite Setup    ${KEYWORD}

    *** Variables ***
    ${GLOBAL}    String with {OTHER_GLOBAL}

    *** Test Cases ***
    Test
        ${local}    Set Variable    variable
        Log    ${local}
        Log    ${GLOBAL}
        Log    ${local['item']}

    *** Keywords ***
    Keyword
        [Arguments]    ${arg}
        Log    ${arg}

    Keyword With ${embedded}
        Log    ${emb_eded}
    ```

???+ note

    RenameVariables is still under development and is not considered a complete feature. The following syntax is not yet supported:

      - variable evaluation with ``${variable * 2}`` (following will be replaced to ``${variable_*_2}``
      - variables passed by variable, not value (``$var``) are ignored

    Robocop can be locally disabled with ``# robocop format: off`` if you want to ignore specific cases.

## Variable case in the Settings section

All variables in the ``*** Settings ***`` section are formatted to uppercase. This behaviour is configurable
using ``settings_section_case``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.settings_section_case=upper
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.settings_section_case=upper"
    ]
    ```

Allowed values are:

- ``upper`` (default) to uppercase names
- ``lower`` to lowercase names
- ``ignore`` to leave an existing case

## Variable case in Variables section

All variables in the ``*** Variables ***`` section are formatted to uppercase. This behaviour is configurable
using ``variables_section_case``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.variables_section_case=upper
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.variables_section_case=upper"
    ]
    ```

Allowed values are:

- ``upper`` (default) to uppercase names
- ``lower`` to lowercase names
- ``ignore`` to leave an existing case

## Variable case in Keywords, Tasks and Test Cases sections

Variable case in ``*** Keywords ***``, ``*** Tasks ***`` and ``*** Test Cases ***`` sections depends on the
variable scope. Local variables are lowercase and global variables are uppercase. Any unknown variable (not defined
in the current keyword or test case) is considered as global. You can configure what should happen with unknown variables using
``unknown_variables_case``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.unknown_variables_case=upper
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.unknown_variables_case=upper"
    ]
    ```

Allowed values are:

- ``upper`` (default) to uppercase unknown names
- ``lower`` to lowercase unknown names
- ``ignore`` to leave an existing case

Scope of the variable can be also changed using ``Set Test/Task/Suite/Global Variable`` keywords and with Robot
Framework 7.0 ``VAR`` syntax using ``scope=local/TEST/TASK/SUITE/GLOBAL`` parameter.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}  # ${arg} is known
        ${local}    Set Variable    value  # since we set it, ${local} is also known
        VAR    ${local2}    value  # default scope is local
        Keyword Call    ${arg}    ${local}    ${local2}    ${global}  # ${global} is unknown
    ```

=== "After (unknown_variables_case = upper)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}  # ${arg} is known
        ${local}    Set Variable    value  # since we set it, ${local} is also known
        VAR    ${local2}    value  # default scope is local
        Keyword Call    ${arg}    ${local}    ${local2}    ${GLOBAL}  # ${global} is unknown
    ```

=== "After (unknown_variables_case = lower)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}  # ${arg} is known
        ${local}    Set Variable    value  # since we set it, ${local} is also known
        VAR    ${local2}    value  # default scope is local
        Keyword Call    ${arg}    ${local}    ${local2}    ${global}  # ${global} is unknown
    ```

=== "After (unknown_variables_case = ignore)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]    ${arg}  # ${arg} is known
        ${local}    Set Variable    value  # since we set it, ${local} is also known
        VAR    ${local2}    value  # default scope is local
        Keyword Call    ${arg}    ${local}    ${local2}    ${global}  # ${global} is unknown
    ```

## Ignore variable case

Case of all variables is converted according to the configured conventions. It is possible to pass the names of the
variables that should be ignored. By default, following variables case is ignored and not formatted:

- ``${\n}``
- ``${None}``
- ``${True}``
- ``${False}``

Configure ``ignore_case`` to ignore an additional list. This parameter accepts a comma-separated list of variable names
(case-sensitive):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.ignore_case=true,LOCAL_THAT_SHOULD_BE_UPPER
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.ignore_case=true,LOCAL_THAT_SHOULD_BE_UPPER"
    ]
    ```

## Converting camelCase to snake_case

Variable names written in camelCase are converted to snake_case. You can disable this behaviour by configuring
``convert_camel_case`` to ``False``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.convert_camel_case=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.convert_camel_case=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Variables ***
    ${camelCase}    value

    *** Keywords ***
    Keyword
        ${CamelCase_Name}    Set Variable    value
        Keyword Call    ${CamelCase_Name}
    ```

=== "After - default (convert_camel_case = True)"

    ```robotframework
    *** Variables ***
    ${camel_case}    value

    *** Keywords ***
    Keyword
        ${camel_case_name}    Set Variable    value
        Keyword Call    ${camel_case_name}
    ```

=== "After (convert_camel_case = False)"

    ```robotframework
    *** Variables ***
    ${CAMELCASE}    value

    *** Keywords ***
    Keyword
        ${camelcase_name}    Set Variable    value
        Keyword Call    ${camelcase_name}
    ```

Renaming from camelCase to snake_case is usually safe except the variables passed as kwargs:

```robotframework
*** Keywords ***
Keyword
    Keyword With Kwargs    processValue=40

Keyword With Kwargs
    [Arguments]    ${with_default}=10    ${processValue}=10
    Should Be Equal    ${with_default}    ${processValue}
```

In such case ``${processValue}`` will be converted to ``${process_value}`` but processValue from keyword call
will not be converted.

## Variable separator

Separators inside variable name are converted to underscore (``_``). You can configure it using ``variable_separator``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameVariables -c RenameVariables.variable_separator=underscore
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameVariables"
    ]
    configure = [
        "RenameVariables.variable_separator=underscore"
    ]
    ```

Allowed values are:

- ``underscore`` (default)
- ``space``
- ``ignore``

=== "Before"

    ```robotframework
    *** Variables ***
    ${camelCase}    value

    *** Keywords ***
    Keyword
        ${variable_name}    Set Variable    value
        Keyword Call    ${variable name}
    ```

=== "After - default (variable_separator = underscore)"

    ```robotframework
    *** Variables ***
    ${CAMEL_CASE}    value

    *** Keywords ***
    Keyword
        ${variable_name}    Set Variable    value
        Keyword Call    ${variable_name}
    ```

=== "After (variable_separator = space)"

    ```robotframework
    *** Variables ***
    ${CAMEL CASE}    value

    *** Keywords ***
    Keyword
        ${variable name}    Set Variable    value
        Keyword Call    ${variable name}
    ```

=== "After (variable_separator = ignore)"

    ```robotframework
    *** Variables ***
    ${CAMEL CASE}    value

    *** Keywords ***
    Keyword
        ${variable_name}    Set Variable    value
        Keyword Call    ${variable name}
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip all instances of a given type
of the code.
