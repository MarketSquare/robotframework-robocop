# Rules list

This is the complete list of all Robocop rules grouped by categories.
If you want to learn more about the rules and their features, see [rules](linter/rules.md).

There are over 190 rules available in Robocop and they are organized into the following categories:

* ARG: [Arguments](#arguments)
* COM: [Comments](#comments)
* DEPR: [Deprecated code](#deprecated-code)
* DOC: [Documentation](#documentation)
* DUP: [Duplications](#duplications)
* ERR: [Errors](#errors)
* GRP: [Groups](#groups)
* IMP: [Imports](#imports)
* KW: [Keywords](#keywords)
* LEN: [Lengths](#lengths)
* MISC: [Miscellaneous](#miscellaneous)
* NAME: [Naming](#naming)
* ORD: [Order](#order)
* SPC: [Spacing](#spacing)
* TAG: [Tags](#tags)
* VAR: [Variables](#variables)
* ANN: [Annotations](#annotations)

Below is the list of all Robocop rules.

## Arguments

Rules for keyword arguments.

### ARG01: unused-argument

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0919

Fix availability: There is no automatic fix.

**Message**:

`Keyword argument '{name}' is not used`

**Documentation**:

Keyword argument was defined but not used:

    *** Keywords ***
    Keyword
        [Arguments]    ${used}    ${not_used}  # will report ${not_used}
        Log    ${used}
        IF    $used
            Log    Escaped syntax is supported.
        END

    Keyword with ${embedded} and ${not_used}  # will report ${not_used}
        Log    ${embedded}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-argument.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-argument.severity=W"
        ]
        ```

---

### ARG02: argument-overwritten-before-usage

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0921

Fix availability: There is no automatic fix.

**Message**:

`Keyword argument '{name}' is overwritten before usage`

**Documentation**:

Keyword argument was overwritten before it is used:

    *** Keywords ***
    Overwritten Argument
        [Arguments]    ${overwritten}  # we do not use ${overwritten} value at all
        ${overwritten}    Set Variable    value  # we only overwrite it

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure argument-overwritten-before-usage.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "argument-overwritten-before-usage.severity=W"
        ]
        ```

---

### ARG03: undefined-argument-default

Added: `v5.7.0`

Supported RF version `All`

Deprecated names: 0932

Fix availability: Fix is always available.

**Message**:

`Undefined argument default, use {arg_name}=${{EMPTY}} instead`

**Documentation**:

Keyword arguments can define a default value. Every time you call the keyword, you can
optionally overwrite this default.

When you use an argument default, you should be as clear as possible. This improves the
readability of your code. The syntax ``${argument}=`` is unclear unless you happen to know
that it is technically equivalent to ``${argument}=${EMPTY}``. To prevent people from
misreading your keyword arguments, explicitly state that the value is empty using the
built-in ``${EMPTY}`` variable.

Example of a rule violation:

    *** Keywords ***
    My Amazing Keyword
        [Arguments]    ${argument_name}=

The fix adds the explicit ``${EMPTY}`` default value.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure undefined-argument-default.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "undefined-argument-default.severity=W"
        ]
        ```

---

### ARG04: undefined-argument-value

Added: `v5.7.0`

Supported RF version `All`

Deprecated names: 0933

Fix availability: There is no automatic fix.

**Message**:

`Undefined argument value, use {arg_name}=${{EMPTY}} instead`

**Documentation**:

When calling a keyword, it can accept named arguments.

When you call a keyword, you should be as clear as possible. This improves the
readability of your code. The syntax ``argument=`` is unclear unless you happen to know
that it is technically equivalent to ``argument=${EMPTY}``. To prevent people from
misreading your keyword arguments, explicitly state that the value is empty using the
built-in ``${EMPTY}`` variable.

If this rule falsely flags your argument, escape the ``=`` character in your argument
value by like so: ``\=``.

Example of a rule violation:

    *** Test Cases ***
    Test case
        My Amazing Keyword    argument_name=

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure undefined-argument-value.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "undefined-argument-value.severity=W"
        ]
        ```

---

### ARG05: invalid-argument

Added: `v1.11.0`

Supported RF version `>=4.0`

Deprecated names: 0407

Fix availability: There is no automatic fix.

**Message**:

`{error_msg}`

**Documentation**:

Argument names should follow variable naming syntax: start with identifier (``$``, ``@`` or ``&``) and enclosed
in curly brackets (``{}``).

Valid names:

    *** Keywords ***
    Keyword
        [Arguments]    ${var}    @{args}    &{config}    ${var}=default

Invalid names:

    *** Keywords ***
    Keyword
        [Arguments]    {var}    @args}    var=default

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-argument.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-argument.severity=E"
        ]
        ```

---

### ARG06: duplicated-argument-name

Added: `v1.11.0`

Supported RF version `All`

Deprecated names: 0811

Fix availability: There is no automatic fix.

**Message**:

`Argument name '{argument_name}' is already used`

**Documentation**:

Argument name is already used.

Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following arguments
are duplicates:

    *** Keywords ***
    Keyword
        [Arguments]    ${var}  ${VAR}  ${v_ar}  ${v ar}
        Other Keyword

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-argument-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-argument-name.severity=W"
        ]
        ```

---

### ARG07: arguments-per-line

Added: `v\-`

Supported RF version `All`

Deprecated names: 0532

Fix availability: There is no automatic fix.

**Message**:

`There is too many arguments per continuation line ({arguments_count} / {max_arguments_count})`

**Documentation**:

Too many arguments per continuation line.

If the keyword's ``[Arguments]`` are split into multiple lines, it is recommended to put only one argument
per every line.

Incorrect code example:

    *** Keywords ***
    Keyword With Multiple Arguments
    [Arguments]    ${first_arg}
    ...    ${second_arg}    ${third_arg}=default

Correct code:

    *** Keywords ***
    Keyword With Multiple Arguments
    [Arguments]    ${first_arg}
    ...    ${second_arg}
    ...    ${third_arg}=default

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure arguments-per-line.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "arguments-per-line.severity=I"
        ]
        ```

??? example "max_args"

    Maximum number of arguments allowed in the continuation line

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure arguments-per-line.max_args=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "arguments-per-line.max_args=1"
        ]
        ```

---

### ARG08: invalid-argument-count

> Rule is disabled by default. Enable it by using ``--select invalid-argument-count`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' expects {expected} but {provided} provided{missing}`

**Documentation**:

Keyword is called with a wrong number of arguments.

Compares the number of arguments used in the keyword call with the ``[Arguments]`` setting of the keyword
definition. Such call fails during the execution.

Example of rule violation:

    *** Test Cases ***
    Test
        Login    user                  # too few arguments
        Login    user    pass    extra # too many arguments

    *** Keywords ***
    Login
        [Arguments]    ${username}    ${password}
        Log    ${username}

Keywords defined in the project are checked using the ``[Arguments]`` setting. Keywords coming from libraries
are checked as well, but only if the library analysis is enabled (it is by default). Robocop imports the
libraries to find out what arguments they accept, which means that the library code is executed. Use the
``--no-analyze-libraries`` option to disable it, or ``--ignored-library`` to skip selected libraries.

To avoid false positives, the call is not reported when:

- the keyword name is built from a variable,
- the keyword is not found in the project, or more than one definition matches the name,
- the keyword uses embedded arguments,
- the call expands a list (``@{args}``) or dictionary (``&{kwargs}``) variable,
- the keyword is used as a test template.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-argument-count.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-argument-count.severity=E"
        ]
        ```

---

### ARG09: missing-argument-name

> Rule is disabled by default. Enable it by using ``--select missing-argument-name`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: Fix is always available.

**Message**:

`Argument '{argument_name}' of the keyword '{keyword_name}' should be passed as a named argument`

**Documentation**:

Keyword is called with a positional argument instead of a named one.

Optional rule for projects that require every keyword to be called with named arguments. Positional arguments
are easy to mix up, especially with keywords that accept a lot of them:

    *** Keywords ***
    Create User
        [Arguments]    ${name}    ${surname}    ${age}    ${city}
        Log Many    ${name}    ${surname}    ${age}    ${city}

    *** Test Cases ***
    Test
        Create User    Bob    Smith    30    Berlin  # will report 4 issues

With this rule enabled, the call should be written as:

    *** Test Cases ***
    Test
        Create User    name=Bob    surname=Smith    age=30    city=Berlin

The rule is not enabled by default. Select it to use it:

    robocop check --select missing-argument-name

Argument names are taken from the keyword definition, so the whole project needs to be analyzed. Keywords
coming from the libraries are ignored by default, since it is not always possible to call them with named
arguments. Configure ``ignore_library_keywords`` to check them as well:

    robocop check --select missing-argument-name --configure missing-argument-name.ignore_library_keywords=False

Calls with only a few arguments are often clear enough. Use ``min_arguments`` to only report calls that use
at least given number of positional arguments:

    robocop check --select missing-argument-name --configure missing-argument-name.min_arguments=3

To avoid false positives, the argument is not reported when:

- the keyword name is built from a variable,
- the keyword is not found in the project, or more than one definition matches the name,
- the keyword uses embedded arguments,
- the call expands a list (``@{args}``) or dictionary (``&{kwargs}``) variable,
- the keyword is used as a test template,
- the argument is passed to ``*varargs``, or the keyword does not accept it as a named argument.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-argument-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-argument-name.severity=W"
        ]
        ```

??? example "ignore_library_keywords"

    Do not report calls of the keywords imported from the libraries

    **Default value:** True

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-argument-name.ignore_library_keywords=True
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-argument-name.ignore_library_keywords=True"
        ]
        ```

??? example "min_arguments"

    Minimal number of the positional arguments in the call required to report it

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-argument-name.min_arguments=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-argument-name.min_arguments=1"
        ]
        ```

## Comments

Rules for comments.

### COM01: todo-in-comment

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0701

Fix availability: There is no automatic fix.

**Message**:

`Found a marker '{marker}' in the comments`

**Documentation**:

TODO-like marker found in the comment.

By default, it reports ``TODO`` and ``FIXME`` markers.

Example:

    # TODO: Refactor this code
    # fixme

Configuration example:

    robocop check --configure "todo-in-comment.markers=todo,Remove me,Fix this!"

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure todo-in-comment.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "todo-in-comment.severity=W"
        ]
        ```

??? example "markers"

    List of case-insensitive markers that violate the rule in comments.

    **Default value:** todo,fixme

    **Type:** comma separated value

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure todo-in-comment.markers=todo,fixme
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "todo-in-comment.markers=todo,fixme"
        ]
        ```

---

### COM02: missing-space-after-comment

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0702

Fix availability: Fix is sometimes available.

**Message**:

`Missing blank space after comment character`

**Documentation**:

No space after the ``#`` character and comment body.

Comments usually start from the new line, or after 2 spaces in the same line. '#' characters denote the start of the
comment, followed by the space and comment body:

    # stand-alone comment
    Keyword Call  # inline comment
    ### block comments are fine ###

Deviating from this pattern may lead to inconsistent or less readable comment format.

It is possible to configure block comments syntax that should be ignored.
Configured regex for block comment should take into account the first character is ``#``.

Example:

    #bad
    # good
    ### good block

Configuration example:

    robocop check --configure missing-space-after-comment.block=^#[*]+

Allows commenting like:

    #*****
    #
    # Important topics here!
    #
    #*****
    or
    #* Headers *#

The fix adds the missing space. Comments that would still violate the rule after adding the space
(such as ``##comment``, which is not recognized as a block comment) are not fixed.

**Style guide**:

- [#comments](https://docs.robotframework.org/docs/style_guide#comments)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-space-after-comment.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-space-after-comment.severity=I"
        ]
        ```

??? example "block"

    Block comment regex pattern.

    **Default value:** ^###

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-space-after-comment.block=^###
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-space-after-comment.block=^###"
        ]
        ```

---

### COM03: invalid-comment

Added: `v1.0.0`

Supported RF version `<4.0`

Deprecated names: 0703

Fix availability: There is no automatic fix.

**Message**:

`Comment starts from the second character in the line`

**Documentation**:

Invalid comment.

In Robot Framework 3.2.2, comments that started from the second character in the line were not recognised as
comments. '#' characters need to be in first or any other than the second character in the line to be recognised
as a comment.

Example:

```text
# good
 # bad
  # third cell so it's good
```

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-comment.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-comment.severity=E"
        ]
        ```

---

### COM04: ignored-data

Added: `v1.3.0`

Supported RF version `All`

Deprecated names: 0704

Fix availability: Fix is sometimes available.

**Message**:

`Ignored data found in file`

**Documentation**:

Ignored data found in the file.

All lines before the first test data section ([ref](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-data-sections))
are ignored. It's recommended to add a `` *** Comments *** `` section header for lines that should be ignored.

Missing section header:

    Resource   file.resource  # it looks like *** Settings *** but section header is missing - line is ignored

    *** Keywords ***
    Keyword Name
       No Operation

Comment lines that should be inside ``*** Comments ***``:

    Deprecated Test
        Keyword
        Keyword 2

    *** Test Cases ***

The fix adds the ``*** Comments ***`` section header before the ignored data. Data containing the language
header is not fixed, since the header would stop working inside the ``*** Comments ***`` section.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure ignored-data.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "ignored-data.severity=W"
        ]
        ```

---

### COM05: bom-encoding-in-file

> Rule is disabled by default. Enable it by using ``--select bom-encoding-in-file`` option.

Added: `v1.7.0`

Supported RF version `All`

Deprecated names: 0705

Fix availability: There is no automatic fix.

**Message**:

`BOM (Byte Order Mark) found in the file`

**Documentation**:

BOM (Byte Order Mark) found in the file.

Some code editors can save Robot file using BOM encoding.
It is not supported by older versions of the Robot Framework.
Ensure that the file is saved in UTF-8 encoding.

Changes in 8.0.0: Rule is now optional since Robot Framework now supports BOM encoding.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure bom-encoding-in-file.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "bom-encoding-in-file.severity=W"
        ]
        ```

---

### COM06: commented-out-code

> Rule is disabled by default. Enable it by using ``--select commented-out-code`` option.

Added: `v7.1.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Commented out code: '{snippet}'`

**Documentation**:

Commented out code detected.

Uses Robot Framework's tokenizer to detect comments that contain RF code syntax.
This approach reliably identifies:

- **Variable assignment**: ``${var}=``, ``@{list}=``, ``&{dict}=``
- **Setting brackets**: ``[Tags]``, ``[Arguments]``, ``[Documentation]``, ``[Setup]``,
  ``[Teardown]``, ``[Template]``, ``[Timeout]``, ``[Return]``
- **Control structures**: ``IF``, ``ELSE``, ``ELSE IF``, ``END``, ``FOR``,
  ``WHILE``, ``TRY``, ``EXCEPT``, ``FINALLY``, ``BREAK``, ``CONTINUE``, ``RETURN``,
  ``GROUP``, ``VAR``
- **Settings section statements**: ``Library``, ``Resource``, ``Variables``,
  ``Suite Setup``, ``Suite Teardown``, ``Test Setup``, ``Test Teardown``,
  ``Metadata``, ``Force Tags``, ``Default Tags``

The following are ignored:

- Comments starting with TODO/FIXME markers (configurable)
- Comments inside ``[Documentation]`` sections (code examples are common there)
- Plain prose comments (e.g., "If you need help" is not detected as IF statement)

This rule is disabled by default. Enable it to detect forgotten or accidentally
commented-out code.

Example of violations:

    Keyword
        # ${result}=    Get Value
        # [Tags]    smoke
        # IF    ${condition}
        Other Keyword

Example of valid comments:

    # This is a normal comment
    # TODO: implement this feature
    # If you need help, ask

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure commented-out-code.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "commented-out-code.severity=W"
        ]
        ```

??? example "markers"

    Markers that indicate legitimate comments (not code). comments starting with these markers are ignored.

    **Default value:** todo,fixme

    **Type:** comma separated value

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure commented-out-code.markers=todo,fixme
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "commented-out-code.markers=todo,fixme"
        ]
        ```

## Deprecated code

Rules for deprecated code or code replacement recommendations.

### DEPR01: if-can-be-used

> **Warning**
>
> Rule is deprecated.

Added: `v1.4.0`

Supported RF version `All`

Deprecated names: 0908

Fix availability: There is no automatic fix.

**Message**:

`'{run_keyword}' can be replaced with IF block since Robot Framework 4.0`

**Documentation**:

``Run Keyword If`` or ``Run Keyword Unless`` used instead of IF.

Starting from Robot Framework 4.0 IF block can be used instead of those keywords.

Changes in 8.9.0: Rule is deprecated. It only supported Robot Framework 4, while Robocop
now requires Robot Framework 5.0+. Use ``deprecated-run-keyword-if`` (DEPR08) instead.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure if-can-be-used.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "if-can-be-used.severity=I"
        ]
        ```

---

### DEPR02: deprecated-statement

> **Warning**
>
> Rule is deprecated.

Added: `v2.0.0`

Supported RF version `All`

Deprecated names: 0319

Fix availability: There is no automatic fix.

**Message**:

`'{statement_name}' is deprecated since Robot Framework version {version}, use '{alternative}' instead`

**Documentation**:

Statement is deprecated.

Detects any piece of code that is marked as deprecated but still works in RF.

For example, ``Run Keyword`` and ``Continue For Loop`` keywords or ``[Return]`` setting.

Changes in 8.0.0: Rule is now split into separate deprecated-* rules and the original rule is deprecated.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-statement.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-statement.severity=W"
        ]
        ```

---

### DEPR03: deprecated-with-name

Added: `v2.5.0`

Supported RF version `>=6.0`

Deprecated names: 0321

Fix availability: Fix is always available.

**Message**:

`Deprecated 'WITH NAME' alias marker used instead of 'AS'`

**Documentation**:

Deprecated 'WITH NAME' alias marker used instead of 'AS'.

``WITH NAME`` marker used when giving an alias to an imported library is going to be renamed to ``AS``.
The motivation is to be consistent with Python that uses ``as`` for a similar purpose.

Incorrect code example:

    *** Settings ***
    Library    Collections    WITH NAME    AliasedName

Correct code:

    *** Settings ***
    Library    Collections    AS    AliasedName

The fix replaces the ``WITH NAME`` marker with ``AS``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-with-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-with-name.severity=W"
        ]
        ```

---

### DEPR04: deprecated-singular-header

Added: `v2.6.0`

Supported RF version `>=6.0`

Deprecated names: 0322

Fix availability: Fix is always available.

**Message**:

`'{singular_header}' deprecated singular header used instead of '{plural_header}'`

**Documentation**:

Deprecated singular header used instead of plural form.

Robot Framework 6.0 starts a deprecation period for singular headers forms. The rationale behind this change
is available at https://github.com/robotframework/robotframework/issues/4431

Incorrect code example:

    *** Setting ***
    *** Keyword ***

Correct code:

    *** Settings ***
    *** Keywords ***

The fix replaces the singular header with the plural one, keeping the original header formatting.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-singular-header.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-singular-header.severity=W"
        ]
        ```

---

### DEPR05: replace-set-variable-with-var

Added: `v5.0.0`

Supported RF version `>=7.0`

Deprecated names: 0327

Fix availability: There is no automatic fix.

**Message**:

`{set_variable_keyword} used instead of VAR`

**Documentation**:

Set X Variable used instead of VAR.

Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
VAR syntax. The VAR syntax is recommended over previously existing keywords.

Incorrect code example:

    *** Keywords ***
    Set Variables To Different Scopes
        Set Local Variable    ${local}    value
        Set Test Variable    ${TEST_VAR}    value
        Set Task Variable    ${TASK_VAR}    value
        Set Suite Variable    ${SUITE_VAR}    value
        Set Global Variable    ${GLOBAL_VAR}    value

Correct code:

    *** Keywords ***
    Set Variables To Different Scopes
        VAR    ${local}    value
        VAR    ${TEST_VAR}    value    scope=TEST
        VAR    ${TASK_VAR}    value    scope=TASK
        VAR    ${SUITE_VAR}    value    scope=SUITE
        VAR    ${GLOBAL_VAR}    value    scope=GLOBAL

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure replace-set-variable-with-var.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "replace-set-variable-with-var.severity=I"
        ]
        ```

---

### DEPR06: replace-create-with-var

Added: `v5.0.0`

Supported RF version `>=7.0`

Deprecated names: 0328

Fix availability: There is no automatic fix.

**Message**:

`{create_keyword} used instead of VAR`

**Documentation**:

Create List/Dictionary used instead of VAR.

Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the
VAR syntax. The VAR syntax is recommended over previously existing keywords.

Incorrect code example:

    *** Keywords ***
    Create Variables
        @{list}    Create List    a  b
        &{dict}    Create Dictionary    key=value

Correct code:

    *** Keywords ***
    Create Variables
        VAR    @{list}    a  b
        VAR    &{dict}    key=value

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure replace-create-with-var.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "replace-create-with-var.severity=I"
        ]
        ```

---

### DEPR07: deprecated-force-tags

Added: `v8.0.0`

Supported RF version `>=6.0`

Fix availability: Fix is always available.

**Message**:

`'Force Tags' is deprecated, use 'Test Tags' instead`

**Documentation**:

Force Tags setting is deprecated.

The following code is deprecated and will be removed in the future:

    *** Settings ***
    Force Tags      tag

Use ``Test Tags`` instead:

    *** Settings ***
    Test Tags      tag

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-force-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-force-tags.severity=W"
        ]
        ```

---

### DEPR08: deprecated-run-keyword-if

Added: `v8.0.0`

Supported RF version `>=4.0`

Fix availability: Fix is sometimes available.

**Message**:

`'{statement_name}' is deprecated, use 'IF' instead`

**Documentation**:

``Run Keyword If`` and ``Run Keyword Unless`` keywords are deprecated.

The following code is deprecated and will be removed in the future:

    *** Test Cases ***
    Test with conditions
        Run Keyword If    ${GLOBAL_FLAG}    Conditional Keyword
        Run Keyword Unless    ${local_value} == "true"    Conditional Keyword
        Run Keyword If  ${condition}
            ...  Keyword  ${arg}
            ...  ELSE IF  ${condition2}  Keyword2
            ...  ELSE  Keyword3

Use ``IF`` instead:

    *** Test Cases ***
    Test with conditions
        IF    ${GLOBAL_FLAG}    Conditional Keyword
        IF    not (${local_value} == "true")    Conditional Keyword
        Keyword
            IF    ${condition}
                Keyword    ${arg}
            ELSE IF    ${condition2}
                Keyword2
            ELSE
                Keyword3
            END

The fix replaces the keyword call with an ``IF`` block. ``Run Keyword Unless`` conditions are wrapped in
``not (...)``. Only keyword calls in the body are fixed - ``Run Keyword If`` used as a setting value
(for example ``Suite Setup`` or ``[Template]``) or without arguments cannot be converted and is left as is.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-run-keyword-if.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-run-keyword-if.severity=W"
        ]
        ```

---

### DEPR09: deprecated-loop-keyword

Added: `v8.0.0`

Supported RF version `>=5.0`

Fix availability: Fix is sometimes available.

**Message**:

`'{statement_name}' is deprecated, use '{alternative}' instead`

**Documentation**:

Loop keywords are deprecated.

The following loop keywords are deprecated:

- ``Continue For Loop``
- ``Continue For Loop If``
- ``Exit For Loop``
- ``Exit For Loop If``

Use ``CONTINUE`` and ``BREAK`` instead.

Incorrect code example:

    *** Test Cases ***
    Test with loops
        WHILE    ${condition}
            Continue For Loop If    ${second_condition}
            Continue For Loop
        END
        FOR    ${var}    IN RANGE    10
            Exit For Loop If    ${var} = 5
            Exit For Loop
        END

Correct code:

    *** Test Cases ***
    Test with loops
        WHILE    ${condition}
            First Keyword
            IF    ${second_condition}    CONTINUE
            CONTINUE
        END
        FOR    ${var}    IN RANGE    10
            IF    ${var} = 0    BREAK
            BREAK
        END

The fix replaces ``Continue For Loop`` with ``CONTINUE`` and ``Exit For Loop`` with ``BREAK``. The
``... If`` variants are wrapped in an ``IF`` block. Only body keyword calls are fixed - the keyword
used as a setting value (for example ``[Setup]`` or ``[Template]``) is left as is.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-loop-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-loop-keyword.severity=W"
        ]
        ```

---

### DEPR10: deprecated-return-keyword

Added: `v8.0.0`

Supported RF version `>=5.0`

Fix availability: Fix is always available.

**Message**:

`'{statement_name}' is deprecated, use '{alternative}' instead`

**Documentation**:

``Return From Keyword`` and ``Return From Keyword If`` keywords are deprecated.

Use ``RETURN`` or ``IF  <condition>  RETURN`` instead.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-return-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-return-keyword.severity=W"
        ]
        ```

---

### DEPR11: deprecated-return-setting

Added: `v8.0.0`

Supported RF version `>=5.0`

Fix availability: Fix is always available.

**Message**:

`'[Return]' is deprecated, use 'RETURN' instead`

**Documentation**:

``[Return]`` settings is deprecated.

Use ``RETURN`` instead.

Incorrect code example:

    *** Keywords ***
    Return One Value
        [Arguments]    ${arg}
        ${value}    Convert To Upper Case    ${arg}
        [Return]    ${value}

Correct code:

    *** Keywords ***
    Return One Value
        [Arguments]    ${arg}
        ${value}    Convert To Upper Case    ${arg}
        RETURN    ${value}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure deprecated-return-setting.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "deprecated-return-setting.severity=I"
        ]
        ```

## Documentation

Rules for documentation.

### DOC01: missing-doc-keyword

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0201

Fix availability: There is no automatic fix.

**Message**:

`Missing documentation in '{name}' keyword`

**Documentation**:

Keyword without documentation.

Keyword documentation is displayed in a tooltip in most code editors,
so it is recommended to write it for each keyword.

You can add documentation to keyword using following syntax:

    *** Keywords ***
    Keyword
        [Documentation]  Keyword documentation
        Keyword Step
        Other Step

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-doc-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-doc-keyword.severity=W"
        ]
        ```

---

### DOC02: missing-doc-test-case

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0202

Fix availability: There is no automatic fix.

**Message**:

`Missing documentation in '{name}' test case`

**Documentation**:

Test case without documentation.

You can add documentation to test case using following syntax:

    *** Test Cases ***
    Test
        [Documentation]  Test documentation
        Keyword Step
        Other Step

The rule by default ignores templated test cases but it can be configured with:

    robocop check --configure missing-doc-test-case.ignore_templated=False

Possible values are: ``Yes`` / ``1`` / ``True`` (default) or ``No`` / ``False`` / ``0``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-doc-test-case.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-doc-test-case.severity=W"
        ]
        ```

??? example "ignore_templated"

    Whether templated tests should be documented or not

    **Default value:** True

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-doc-test-case.ignore_templated=True
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-doc-test-case.ignore_templated=True"
        ]
        ```

---

### DOC03: missing-doc-suite

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0203

Fix availability: There is no automatic fix.

**Message**:

`Missing documentation in suite`

**Documentation**:

Test suite without documentation.

You can add documentation to suite using following syntax:

    *** Settings ***
    Documentation    Suite documentation

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-doc-suite.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-doc-suite.severity=W"
        ]
        ```

---

### DOC04: missing-doc-resource-file

Added: `v2.8.0`

Supported RF version `All`

Deprecated names: 0204

Fix availability: There is no automatic fix.

**Message**:

`Missing documentation in resource file`

**Documentation**:

Resource file without documentation.

You can add documentation to resource file using following syntax:

    *** Settings ***
    Documentation    Resource file documentation

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-doc-resource-file.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-doc-resource-file.severity=W"
        ]
        ```

---

### DOC05: variable-in-documentation

> Rule is disabled by default. Enable it by using ``--select variable-in-documentation`` option.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Unescaped variable '{variable}' in documentation`

**Documentation**:

Unescaped variable syntax in documentation.

Robot Framework resolves variables in suite, test case and user keyword documentation when a suite is executed.
This includes scalar (``${name}``), list (``@{items}``), dictionary (``&{mapping}``) and environment
(``%{NAME}``) variable syntax. Defined variables are replaced with their values. Undefined variables are left
unchanged, which can make an unescaped literal example appear correct until a variable with the same name becomes
available.

For example, this documentation changes at runtime if ``${value}`` exists:

    *** Test Cases ***
    Example
        [Documentation]    The argument syntax is ${value}.
        No Operation

Escape syntax that should be displayed literally:

    *** Test Cases ***
    Example
        [Documentation]    Scalar: \${value}; list: \@{items}; dictionary: \&{mapping}; environment: \%{HOME}.
        No Operation

The leading backslash prevents substitution and is removed from the rendered documentation. The rule checks suite,
test case and user keyword documentation, including continuation lines.

The rule is disabled by default. Enable it with:

    robocop check --select variable-in-documentation

There is no automatic fix. Robocop cannot determine whether interpolation is intentional, and escaping an
intentionally dynamic value would change the rendered documentation. If interpolation is intended, leave the
syntax unescaped and disable the rule locally where needed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure variable-in-documentation.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "variable-in-documentation.severity=I"
        ]
        ```

## Duplications

Rules for duplicated code such as settings or variables.

### DUP01: duplicated-test-case

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0801

Fix availability: There is no automatic fix.

**Message**:

`Multiple test cases with name '{name}' (first occurrence in line {first_occurrence_line})`

**Documentation**:

Multiple test cases with the same name in the suite.

It is not allowed to reuse the same name of the test case within the same suite in Robot Framework.
Name matching is case-insensitive and ignores spaces and underscore characters.

Incorrect code example:

    *** Test Cases ***
    Test with name
        No Operation

    test_with Name
        No Operation

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-test-case.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-test-case.severity=E"
        ]
        ```

---

### DUP02: duplicated-keyword

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0802

Fix availability: There is no automatic fix.

**Message**:

`Multiple keywords with name '{name}' (first occurrence in line {first_occurrence_line})`

**Documentation**:

Multiple keywords with the same name in the file.

Do not define keywords with the same name inside the same file. Name matching is case-insensitive and
ignores spaces and underscore characters.

Incorrect code example:

    *** Keywords ***
    Keyword
        No Operation

    keyword
        No Operation

    K_eywor d
        No Operation

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-keyword.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-keyword.severity=E"
        ]
        ```

---

### DUP03: duplicated-variable

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0803

Fix availability: Fix is always available.

**Message**:

`Multiple variables with name '{name}' in Variables section (first occurrence in line {first_occurrence_line})`

**Documentation**:

Multiple variables with the same name in the file.

Variable names in Robot Framework are case-insensitive and ignore spaces and underscores. Following variables
are duplicates:

    *** Variables ***
    ${variable}    1
    ${VARIAble}    a
    @{variable}    a  b
    ${v ariabl e}  c
    ${v_ariable}   d

Only the first definition is used by Robot Framework, so the duplicated definitions can be safely removed
with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-variable.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-variable.severity=E"
        ]
        ```

---

### DUP04: duplicated-resource

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0804

Fix availability: Fix is always available.

**Message**:

`Multiple resource imports with path '{name}' (first occurrence in line {first_occurrence_line})`

**Documentation**:

Duplicated resource imports.

Avoid re-importing the same imports.

Incorrect code example:

    *** Settings ***
    Resource    path.resource
    Resource    other_path.resource
    Resource    path.resource

The fix removes the duplicated import.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-resource.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-resource.severity=W"
        ]
        ```

---

### DUP05: duplicated-library

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0805

Fix availability: Fix is always available.

**Message**:

`Multiple library imports with name '{name}' and identical arguments (first occurrence in line {first_occurrence_line})`

**Documentation**:

Duplicated library imports.

If you need to reimport library use alias:

    *** Settings ***
    Library  RobotLibrary
    Library  RobotLibrary  AS  OtherRobotLibrary

The fix removes the duplicated import. Only imports with the same name, arguments and alias are reported.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-library.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-library.severity=W"
        ]
        ```

---

### DUP06: duplicated-metadata

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0806

Fix availability: There is no automatic fix.

**Message**:

`Duplicated metadata '{name}' (first occurrence in line {first_occurrence_line})`

**Documentation**:

Duplicated metadata.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-metadata.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-metadata.severity=W"
        ]
        ```

---

### DUP07: duplicated-variables-import

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0807

Fix availability: Fix is always available.

**Message**:

`Duplicated variables import with path '{name}' (first occurrence in line {first_occurrence_line})`

**Documentation**:

Duplicated variables import.

The fix removes the duplicated import.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-variables-import.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-variables-import.severity=W"
        ]
        ```

---

### DUP08: section-already-defined

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0808

Fix availability: There is no automatic fix.

**Message**:

`'{section_name}' section header already defined in file (first occurrence in line {first_occurrence_line})`

**Documentation**:

Section header already defined in the file.

Duplicated section in the file. Robot Framework will handle repeated sections but it is recommended to not
duplicate them.

Incorrect code example:

    *** Test Cases ***
    My Test
        Keyword

    *** Keywords ***
    Keyword
        No Operation

    *** Test Cases ***  # duplicate
    Other Test
        Keyword

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure section-already-defined.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "section-already-defined.severity=I"
        ]
        ```

---

### DUP09: both-tests-and-tasks

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0810

Fix availability: There is no automatic fix.

**Message**:

`Both Task(s) and Test Case(s) section headers defined in file`

**Documentation**:

Both Task(s) and Test Case(s) section headers defined in file.

The file contains both ``*** Test Cases ***`` and ``*** Tasks ***`` sections. Use only one of them. :

    *** Test Cases ***

    *** Tasks ***

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure both-tests-and-tasks.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "both-tests-and-tasks.severity=E"
        ]
        ```

---

### DUP10: duplicated-setting

Added: `v2.0`

Supported RF version `All`

Deprecated names: 0813

Fix availability: There is no automatic fix.

**Message**:

`{error_msg}`

**Documentation**:

Duplicated setting.

Some settings can be used only once in a file. Only the first value is used.

Example:

    *** Settings ***
    Test Tags        F1
    Test Tags        F2  # this setting will be ignored

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-setting.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-setting.severity=W"
        ]
        ```

---

### DUP11: duplicated-variable-in-project

> Rule is disabled by default. Enable it by using ``--select duplicated-variable-in-project`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Variable '{name}' is also defined in '{first_source}' (line {first_occurrence_line})`

**Documentation**:

Variable with the same name defined in multiple files visible together.

Robot Framework does not report an error when the same variable is defined in a suite and in a resource file
imported by it, or in two resource files imported by the same suite. The value used at runtime depends on the
import order, which makes such duplications a common source of hard to debug problems.

Example of rule violation:

    *** Settings ***
    Resource    variables.resource

    *** Variables ***
    ${BROWSER}    firefox  # variables.resource also defines ${BROWSER}

Only variables defined in the ``*** Variables ***`` section are compared. Variable names are normalized, so
``${my var}``, ``${MY_VAR}`` and ``${myvar}`` are treated as the same variable.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-variable-in-project.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-variable-in-project.severity=W"
        ]
        ```

## Errors

Rules for syntax errors and critical issues with the code.

### ERR01: parsing-error

Added: `v1.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Robot Framework syntax error: {error_msg}`

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure parsing-error.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "parsing-error.severity=E"
        ]
        ```

---

### ERR03: missing-keyword-name

Added: `v1.8.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Missing keyword name when calling some values`

**Documentation**:

Missing keyword name.

Example of rule violation:

    *** Keywords ***
    Keyword
        ${var}
        ${one}      ${two}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-keyword-name.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-keyword-name.severity=E"
        ]
        ```

---

### ERR04: variables-import-with-args

Added: `v1.11.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`YAML variable files do not take arguments`

**Documentation**:

YAML variables file import with arguments.

Example of rule violation:

    *** Settings ***
    Variables    vars.yaml        arg1
    Variables    variables.yml    arg2
    Variables    module           arg3  # valid from RF > 5

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure variables-import-with-args.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "variables-import-with-args.severity=E"
        ]
        ```

---

### ERR05: invalid-continuation-mark

Added: `v1.11.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Invalid continuation mark '{mark}'. It should be '...'`

**Documentation**:

Invalid continuation mark.

Example of rule violation:

    Keyword
    ..  ${var}  # .. instead of ...
    ...  1
    ....  2  # .... instead of ...

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-continuation-mark.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-continuation-mark.severity=E"
        ]
        ```

---

### ERR08: non-existing-setting

Added: `v1.11.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`{error_msg}`

**Documentation**:

Non-existing setting used in the code.

Example of rule violation:

   *** Test Cases ***
   Test case
       [Not Existing]  arg
       [Arguments]  ${arg}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure non-existing-setting.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "non-existing-setting.severity=E"
        ]
        ```

---

### ERR09: setting-not-supported

Added: `v1.11.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Setting '[{setting_name}]' is not supported in {test_or_keyword}. Allowed are: {allowed_settings}`

**Documentation**:

Not supported setting.

The following settings are supported in Test Case or Task:

    *** Test Cases ***
    Test case
        [Documentation]      Used for specifying a test case documentation.
        [Tags]               Used for tagging test cases.
        [Setup]              Used for specifying a test setup.
        [Teardown]       Used for specifying a test teardown.
        [Template]       Used for specifying a template keyword.
        [Timeout]        Used for specifying a test case timeout.

The following settings are supported in Keyword:

    *** Keywords ***
    Keyword
        [Documentation]      Used for specifying a user keyword documentation.
        [Tags]               Used for specifying user keyword tags.
        [Arguments]      Used for specifying user keyword arguments.
        [Return]         Used for specifying user keyword return values.
        [Teardown]       Used for specifying user keyword teardown.
        [Timeout]        Used for specifying a user keyword timeout.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure setting-not-supported.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "setting-not-supported.severity=E"
        ]
        ```

---

### ERR12: invalid-for-loop

Added: `v1.0.0`

Supported RF version `>=4.0`

Fix availability: There is no automatic fix.

**Message**:

`Invalid for loop syntax: {error_msg}`

**Documentation**:

Invalid FOR loop syntax.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-for-loop.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-for-loop.severity=E"
        ]
        ```

---

### ERR13: invalid-if

Added: `v1.0.0`

Supported RF version `>=4.0`

Fix availability: There is no automatic fix.

**Message**:

`Invalid IF syntax: {error_msg}`

**Documentation**:

Invalid IF syntax.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-if.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-if.severity=E"
        ]
        ```

---

### ERR14: return-in-test-case

Added: `v2.0.0`

Supported RF version `>=5.0`

Fix availability: There is no automatic fix.

**Message**:

`RETURN can only be used inside a user keyword`

**Documentation**:

RETURN used outside the user keyword.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure return-in-test-case.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "return-in-test-case.severity=E"
        ]
        ```

---

### ERR15: invalid-section-in-resource

Added: `v3.1.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Resource file can't contain '{section_name}' section`

**Documentation**:

Resource file with a not supported section.

The higher-level structure of resource files is the same as that of test case files,
but they can't contain Test Cases or Tasks sections.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-section-in-resource.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-section-in-resource.severity=E"
        ]
        ```

---

### ERR16: invalid-setting-in-resource

Added: `v3.3.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Settings section in resource file can't contain '{section_name}' setting`

**Documentation**:

Not supported setting in the `` *** Settings ***`` section in a resource file.

The Setting section in resource files can contain only import settings (``Library``,
``Resource``, ``Variables``), ``Documentation`` and ``Keyword Tags``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-setting-in-resource.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-setting-in-resource.severity=E"
        ]
        ```

---

### ERR17: unsupported-setting-in-init-file

Added: `v3.3.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Setting '{setting}' is not supported in initialization files`

**Documentation**:

Not supported setting in a initialization file.

Settings ``Default Tags`` and ``Test Template`` are not supported in initialization files.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unsupported-setting-in-init-file.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unsupported-setting-in-init-file.severity=E"
        ]
        ```

## Groups

Rules for the GROUP syntax.

### GRP01: too-few-calls-in-group

Added: `v9.0.0`

Supported RF version `>=7.2`

Fix availability: There is no automatic fix.

**Message**:

`GROUP '{group_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})`

**Documentation**:

Too few keyword calls in a ``GROUP``.

``GROUP`` blocks are meant to group several related steps together. A group with just a single keyword call
usually does not add any value and only introduces an extra level of indentation. Consider inlining the keyword
or adding the missing steps:

    *** Test Cases ***
    Test
        GROUP    Login
            Log In    ${user}    ${password}    # a single keyword does not need a group
        END

An empty ``GROUP`` is a Robot Framework syntax error and is reported by the ``parsing-error`` rule instead.

The number of required keyword calls can be configured with the ``min_calls`` parameter:

    robocop check --configure too-few-calls-in-group.min_calls=3

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `min_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `min_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-group.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-group.severity=W"
        ]
        ```

??? example "min_calls"

    Number of keyword calls required in a group

    **Default value:** 2

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-group.min_calls=2
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-group.min_calls=2"
        ]
        ```

---

### GRP02: too-many-calls-in-group

Added: `v9.0.0`

Supported RF version `>=7.2`

Fix availability: There is no automatic fix.

**Message**:

`GROUP '{group_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})`

**Documentation**:

Too many keyword calls in a ``GROUP``.

A ``GROUP`` that contains a lot of keyword calls is hard to read. Consider splitting it into smaller groups or
extracting the logic into a separate keyword.

The number of allowed keyword calls can be configured with the ``max_calls`` parameter:

    robocop check --configure too-many-calls-in-group.max_calls=20

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-group.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-group.severity=W"
        ]
        ```

??? example "max_calls"

    Number of keyword calls allowed in a group

    **Default value:** 10

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-group.max_calls=10
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-group.max_calls=10"
        ]
        ```

---

### GRP03: group-without-name

Added: `v9.0.0`

Supported RF version `>=7.2`

Fix availability: There is no automatic fix.

**Message**:

`GROUP does not have a name`

**Documentation**:

``GROUP`` used without a name.

A ``GROUP`` can be created without a name, but naming it documents the intent of the grouped steps and makes
the log easier to read:

    *** Test Cases ***
    Test
        GROUP    # will be reported
            Log    message
        END

Correct code example:

    *** Test Cases ***
    Test
        GROUP    Prepare data
            Log    message
        END

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure group-without-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "group-without-name.severity=W"
        ]
        ```

---

### GRP04: nested-group

> Rule is disabled by default. Enable it by using ``--select nested-group`` option.

Added: `v9.0.0`

Supported RF version `>=7.2`

Fix availability: There is no automatic fix.

**Message**:

`GROUP '{group_name}' is nested in another GROUP`

**Documentation**:

``GROUP`` nested inside another ``GROUP``.

Nesting groups makes the code harder to read and is rarely needed. Consider flattening the groups or extracting
the nested group into a separate keyword:

    *** Test Cases ***
    Test
        GROUP    Outer
            GROUP    Inner    # will be reported
                Log    message
            END
        END

This rule is disabled by default. Enable it with ``--select nested-group``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure nested-group.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "nested-group.severity=W"
        ]
        ```

---

### GRP05: group-not-allowed

> Rule is disabled by default. Enable it by using ``--select group-not-allowed`` option.

Added: `v9.0.0`

Supported RF version `>=7.2`

Fix availability: There is no automatic fix.

**Message**:

`GROUP syntax is not allowed`

**Documentation**:

``GROUP`` syntax is not allowed.

The ``GROUP`` syntax was introduced in Robot Framework 7.2. Use this rule to forbid it, for example when your
project needs to stay compatible with older Robot Framework versions or when your team decided not to use groups:

    *** Test Cases ***
    Test
        GROUP    Login    # will be reported
            Log    message
        END

This rule is disabled by default. Enable it with ``--select group-not-allowed``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure group-not-allowed.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "group-not-allowed.severity=W"
        ]
        ```

## Imports

Rules for resources, variables and libraries imports.

### IMP01: wrong-import-order

Added: `v1.7.0`

Supported RF version `All`

Deprecated names: 0911

Fix availability: Fix is always available.

**Message**:

`BuiltIn library import '{builtin_import}' should be placed before '{custom_import}'`

**Documentation**:

Built-in imports placed after custom imports.

To make code more readable, it needs to be more consistent. That's why it is recommended to group known, built-in
import before custom imports.

Example of rule violation:

    *** Settings ***
    Library    Collections
    Library    CustomLibrary
    Library    OperatingSystem  # BuiltIn library defined after custom CustomLibrary

The import can be moved before the first custom import automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-import-order.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-import-order.severity=I"
        ]
        ```

---

### IMP02: builtin-imports-not-sorted

Added: `v5.2.0`

Supported RF version `All`

Deprecated names: 0926

Fix availability: Fix is always available.

**Message**:

`BuiltIn library import '{builtin_import}' should be placed before '{previous_builtin_import}'`

**Documentation**:

Built-in imports are not sorted in alphabetical order.

To increase readability, sort the imports in alphabetical order.

Example of rule violation:

    *** Settings ***
    Library    OperatingSystem
    Library    Collections  # BuiltIn libraries imported not in alphabetical order

The imports can be sorted automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure builtin-imports-not-sorted.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "builtin-imports-not-sorted.severity=I"
        ]
        ```

---

### IMP03: non-builtin-imports-not-sorted

> Rule is disabled by default. Enable it by using ``--select non-builtin-imports-not-sorted`` option.

Added: `v5.2.0`

Supported RF version `All`

Deprecated names: 10101

Fix availability: There is no automatic fix.

**Message**:

`Non builtin library import '{custom_import}' should be placed before '{previous_custom_import}'`

**Documentation**:

Custom imports are not sorted in alphabetical order.

To increase readability, sort the imports in alphabetical order. Beware that depending on your code, some of the
custom imports may be depending on each other and the order of the imports.

Example of rule violation:

    *** Settings ***
    Library    Collections
    Library    CustomLibrary
    Library    AnotherCustomLibrary  # AnotherCustomLibrary library defined after custom CustomLibrary

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure non-builtin-imports-not-sorted.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "non-builtin-imports-not-sorted.severity=W"
        ]
        ```

---

### IMP04: resources-imports-not-sorted

> Rule is disabled by default. Enable it by using ``--select resources-imports-not-sorted`` option.

Added: `v5.2.0`

Supported RF version `All`

Deprecated names: 10102

Fix availability: There is no automatic fix.

**Message**:

`Resource import '{resource_import}' should be placed before '{previous_resource_import}'`

**Documentation**:

Resources imports are not sorted in alphabetical order.

To increase readability, sort the resources imports in a alphabetical order. Beware that depending on your code,
some imports may depend on each other and the order of the imports.

Example of rule violation:

    *** Settings ***
    Resource   CustomResource.resource
    Resource   AnotherFile.resource

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure resources-imports-not-sorted.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "resources-imports-not-sorted.severity=W"
        ]
        ```

---

### IMP05: unused-resource-import

> Rule is disabled by default. Enable it by using ``--select unused-resource-import`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Imported resource file '{import_name}' is not used`

**Documentation**:

Imported resource file is not used.

Reports resource imports whose keywords and variables are never used in the importing file.

Example of rule violation:

    *** Settings ***
    Resource    unused.resource  # nothing from this file is used

    *** Test Cases ***
    Test
        Keyword From Other Resource

A resource is considered used when the file uses any keyword or variable defined in it, or in any resource it
imports itself, since resource imports are transitive in Robot Framework.

To avoid false positives, imports are not reported when:

- the importing file calls a keyword using a name built from a variable, because such call may come from any
  resource,
- the import path could not be resolved,
- the imported resource defines no keywords and no variables, because it may be imported only for the imports
  it makes itself.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-resource-import.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-resource-import.severity=I"
        ]
        ```

---

### IMP06: unused-library-import

> Rule is disabled by default. Enable it by using ``--select unused-library-import`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Imported library '{import_name}' is not used`

**Documentation**:

Imported library is not used.

Reports library imports whose keywords are never used in the importing file.

Example of rule violation:

    *** Settings ***
    Library    Collections  # no keyword from this library is used

    *** Test Cases ***
    Test
        Log    message

Keywords from a library imported in a resource file are available in every file importing that resource,
so the import is reported only when none of those files use any of its keywords.

The library is imported to find out what keywords it provides, which means this rule is only reported when
the library analysis is enabled (see the ``analyze-libraries`` option).

To avoid false positives, imports are not reported when:

- the library could not be imported, or is excluded with the ``ignored-libraries`` option,
- the library provides no keywords, since it may be imported for its side effects, for example to register
  a listener,
- the importing file calls a keyword using a name built from a variable, because such call may come from any
  library,
- the import path or arguments could not be resolved.

Libraries used only through ``Get Library Instance`` or imported dynamically with ``Import Library`` are
reported, since such usage cannot be detected from the source code.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-library-import.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-library-import.severity=I"
        ]
        ```

---

### IMP07: unresolved-resource-import

> Rule is disabled by default. Enable it by using ``--select unresolved-resource-import`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Imported resource file '{import_name}' does not exist`

**Documentation**:

Imported resource file does not exist.

Reports resource imports that point to a file that cannot be found in the project. Such import makes the whole
suite fail during the execution.

Example of rule violation:

    *** Settings ***
    Resource    does_not_exist.resource  # file is not found next to the importing file

Import paths are resolved relative to the file containing the import, exactly like Robot Framework does it.

Variables used in the import path are resolved using variables defined in the ``*** Variables ***`` section
of the importing file and variables provided with the ``--variable`` option::

    robocop check --variable RESOURCE_DIR:resources

If the path contains a variable that cannot be resolved, the import is ignored and not reported. Thanks to that,
dynamically built paths do not cause false positives.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unresolved-resource-import.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unresolved-resource-import.severity=W"
        ]
        ```

---

### IMP08: circular-import

> Rule is disabled by default. Enable it by using ``--select circular-import`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Circular import: {cycle}`

**Documentation**:

Resource file is a part of a circular import.

Reports resource imports that import, directly or indirectly, the file they are used in.

Example of rule violation:

    # keywords.resource
    *** Settings ***
    Resource    helpers.resource

    # helpers.resource
    *** Settings ***
    Resource    keywords.resource  # keywords.resource imports this file already

Robot Framework does not fail on circular imports, but they make it harder to tell where a keyword comes from
and often mean that the files should be split differently. Move the shared keywords to a separate resource file
imported by both files to break the cycle.

Every import taking part in the cycle is reported, together with the path leading back to the importing file.
A file importing itself is reported as well.

Imports that could not be resolved are not reported, since it is not known what they point to.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure circular-import.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "circular-import.severity=W"
        ]
        ```

---

### IMP09: unresolved-library-import

> Rule is disabled by default. Enable it by using ``--select unresolved-library-import`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Imported library '{import_name}' could not be imported: {error}`

**Documentation**:

Imported library could not be imported.

Reports library imports that Robot Framework would not be able to import during the execution.

Example of rule violation:

    *** Settings ***
    Library    libs/does_not_exist.py  # file is not found next to the importing file
    Library    NotInstalledLibrary  # module is not installed and is not found in the search paths

Library imports pointing to a file are always validated. Imports using a module name are only validated when
Robocop imports the libraries, which it does by default and which can be disabled with the
``--no-analyze-libraries`` option::

    robocop check --no-analyze-libraries

Extra directories with the libraries can be provided with the ``--pythonpath`` option::

    robocop check --pythonpath libs

Following imports are never reported, since it is not known if they can be imported:

- imports with a name or arguments containing a variable that cannot be resolved,
- libraries excluded from the analysis with the ``--ignored-library`` option,
- the ``Remote`` library, which connects to the remote server already during the import.

Libraries that require a running service or a special environment can be excluded from the analysis::

    robocop check --ignored-library CustomServiceLibrary

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unresolved-library-import.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unresolved-library-import.severity=W"
        ]
        ```

## Keywords

Rules for keywords.

### KW01: sleep-keyword-used

> Rule is disabled by default. Enable it by using ``--select sleep-keyword-used`` option.

Added: `v5.0.0`

Supported RF version `All`

Deprecated names: 10001

Fix availability: There is no automatic fix.

**Message**:

`Sleep keyword with '{duration_time}' sleep time found`

**Documentation**:

``Sleep`` keyword used.

Avoid using Sleep keyword in favour of polling.

For example:

    *** Keywords ***
    Add To Cart
        [Arguments]    ${item_name}
        Sleep    30s  # wait for page to load
        Element Should Be Visible    ${MAIN_HEADER}
        Click Element    //div[@name='${item_name}']/div[@id='add_to_cart']

Can be rewritten to:

    *** Keywords ***
    Add To Cart
        [Arguments]    ${item_name}
        Wait Until Element Is Visible    ${MAIN_HEADER}
        Click Element    //div[@name='${item_name}']/div[@id='add_to_cart']

It is also possible to report only if ``Sleep`` exceeds given time limit using ``max_time`` parameter:

    robocop check -c sleep-keyword-used.max_time=1min .

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure sleep-keyword-used.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "sleep-keyword-used.severity=W"
        ]
        ```

??? example "max_time"

    Maximum amount of time allowed in sleep

    **Default value:** 0

    **Type:** timestr_to_secs

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure sleep-keyword-used.max_time=0
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "sleep-keyword-used.max_time=0"
        ]
        ```

---

### KW02: not-allowed-keyword

> Rule is disabled by default. Enable it by using ``--select not-allowed-keyword`` option.

Added: `v5.1.0`

Supported RF version `All`

Deprecated names: 10002

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword}' is not allowed`

**Documentation**:

Reports usage of not allowed keywords.

Configure which keywords should be reported by using ``keywords`` parameter.
Keyword names are normalized to match Robot Framework search behaviour (lower case, removed whitespace and
underscores).

For example:

    > robocop check --select not-allowed-keyword -c not-allowed-keyword.keywords=click_using_javascript

: # TODO

    *** Keywords ***
    Keyword With Obsolete Implementation
        [Arguments]    ${locator}
        Click Using Javascript    ${locator}  # Robocop will report not allowed keyword

If keyword call contains possible library name (i.e. Library.Keyword Name), Robocop checks if it matches
the not allowed keywords and if not, it will remove library part and check again.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-keyword.severity=W"
        ]
        ```

??? example "keywords"

    Comma separated list of not allowed keywords

    **Default value:** None

    **Type:** comma_separated_list

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-keyword.keywords=None
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-keyword.keywords=None"
        ]
        ```

---

### KW03: no-embedded-keyword-arguments

> Rule is disabled by default. Enable it by using ``--select no-embedded-keyword-arguments`` option.

Added: `v5.5.0`

Supported RF version `All`

Deprecated names: 10003

Fix availability: There is no automatic fix.

**Message**:

`Keyword with embedded arguments: {arguments}`

**Documentation**:

Embedded arguments in keyword found.

Avoid using embedded arguments in keywords.

When using embedded keyword arguments, you mix what you do (the keyword name) with the data
related to the action (the arguments). Mixing these two concepts can create
hard-to-understand code, which can result in mistakes in your test code.

Embedded keyword arguments can also make it hard to understand which keyword you're using.
Sometimes even Robotframework gets confused when naming conflicts occur. There are ways to
fix naming conflicts, but this adds unnecessary complexity to your keyword.

To prevent these issues, use normal arguments instead.

Using a keyword with one embedded argument. Buying the drink and the size of the drink are
jumbled together:

    *** Test Cases ***
    Prepare for an amazing movie
        Buy a large soda

    *** Keywords ***
    Buy a ${size} soda
        # Do something wonderful

Change the embedded argument to a normal argument. Now buying the drink is separate from the
size of the drink. In this approach, it's easier to see that you can change the size of your
drink:

    *** Test Cases ***
    Prepare for an amazing movie
        Buy a soda    size=large

    *** Keywords ***
    Buy a soda
        [Arguments]    ${size}
        # Do something wonderful

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure no-embedded-keyword-arguments.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "no-embedded-keyword-arguments.severity=W"
        ]
        ```

---

### KW04: unused-keyword

> Rule is disabled by default. Enable it by using ``--select unused-keyword`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v5.3.0`

Supported RF version `All`

Deprecated names: 10101

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' is not used`

**Documentation**:

Keyword is not used.

Reports keywords that are defined in the project but never called.

Example:

    *** Test Cases ***
    Test that only non used keywords are reported
        Used Keyword

    *** Keywords ***
    Used Keyword
        Log    used

    Not Used Keyword  # this keyword will be reported as not used
        [Arguments]    ${arg}
        Should Be True    ${arg}>50

A keyword is considered used when it is called anywhere in the project, including test setups, teardowns and
templates, and keywords nested in ``Run Keyword`` variants. Keywords marked with the ``robot:private`` tag can
only be used in the file they are defined in, so only calls from that file are taken into account.

To avoid false positives, a keyword is not reported when it may be called with a name built from a variable.
For example, a call to ``Login ${type}`` marks both ``Login Admin`` and ``Login User`` as used.

Keywords are only searched for in the files scanned by Robocop. If the project is a shared library of keywords
used by other projects, all of its keywords are reported as not used.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-keyword.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-keyword.severity=I"
        ]
        ```

---

### KW05: keyword-not-found

> Rule is disabled by default. Enable it by using ``--select keyword-not-found`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' not found`

**Documentation**:

Keyword is not defined anywhere.

Reports keyword calls that do not match any keyword defined in the file, in the imported resource files or in
the imported libraries. Robot Framework fails such call with the ``No keyword with name 'X' found`` error.

Example of rule violation:

    *** Settings ***
    Resource    login.resource   # defines Login

    *** Test Cases ***
    Test
        Login    user    password
        Logout                    # Logout is not defined anywhere

Keywords come from libraries more often than not, so this rule requires the library analysis and is only
executed together with the ``--analyze-libraries`` option::

    robocop check --select keyword-not-found --analyze-libraries

To avoid false positives, calls are not reported when the keywords available in the file are not fully known:

- the keyword name is built from a variable,
- any import of the file or of the resources it imports could not be resolved,
- any imported library could not be imported, for example because it is not installed or its arguments could
  not be resolved,
- the file or any of the imported resources imports libraries or resources dynamically, using the
  ``Import Library`` or ``Import Resource`` keywords.

Libraries excluded with the ``--ignored-library`` option make all files importing them skipped as well.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-not-found.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-not-found.severity=E"
        ]
        ```

---

### KW06: ambiguous-keyword-name

> Rule is disabled by default. Enable it by using ``--select ambiguous-keyword-name`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' matches keywords from multiple sources: {sources}`

**Documentation**:

Keyword name matches more than one keyword.

Reports keyword calls that match keywords defined in more than one place. Robot Framework fails such call
with the ``Multiple keywords with name 'X' found`` error, unless the call uses the full name of the keyword.

Example of rule violation:

    *** Settings ***
    Resource    login.resource      # defines Login
    Resource    admin.resource      # defines Login as well

    *** Test Cases ***
    Test
        Login    user    password   # it is not known which keyword should be used

Robot Framework resolves conflicts using the following order, which the rule follows as well:

- a keyword defined in the file containing the call is always used,
- keywords from resource files are used before keywords from libraries,
- a keyword from a custom library is used before a keyword from a standard library.

Calls using the full name of the keyword (``login.Login``) are not reported, since the prefix already
selects the keyword. Calls with a name built from a variable are not reported either.

Keywords defined twice in the same file are reported by the ``duplicated-keyword-name`` rule instead.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure ambiguous-keyword-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "ambiguous-keyword-name.severity=W"
        ]
        ```

---

### KW07: missing-keyword-prefix

> Rule is disabled by default. Enable it by using ``--select missing-keyword-prefix`` option.

> **Project rule**
>
> This rule requires parsing the whole project. Selecting it makes ``robocop check`` analyze the project.
> See [project checks](linter/linter.md#project-checks) for details.

Added: `v9.0.0`

Supported RF version `All`

Fix availability: Fix is always available.

**Message**:

`Keyword '{keyword_name}' should be called with the '{prefix}' prefix`

**Documentation**:

Keyword is called without the name of the resource file or library it comes from.

Optional rule for projects that require every keyword call to be prefixed with the source of the keyword.
Such calls are unambiguous and it is immediately clear where the keyword comes from:

    *** Settings ***
    Resource       login.resource
    Library        SeleniumLibrary

    *** Test Cases ***
    Test
        Login    user    password        # will be reported
        Click Element    id:submit       # will be reported

        login.Login    user    password  # explicit, not reported
        SeleniumLibrary.Click Element    id:submit

The rule is not enabled by default. Select it to use it:

    robocop check --select missing-keyword-prefix

Libraries imported with the ``AS`` (``WITH NAME``) syntax are expected to be called using the alias.
Keywords defined in the file with the call are never reported, since there is nothing to prefix them with.

``BuiltIn`` keywords are not reported by default. Configure ``ignored_sources`` with a comma separated list of
resource file, library and alias names to change it:

    robocop check --select missing-keyword-prefix -c missing-keyword-prefix.ignored_sources=BuiltIn,Collections

To avoid false positives, the call is not reported when:

- the keyword name is built from a variable,
- the keyword name already contains a dot, since it may be prefixed already,
- the keyword is not found in the project, or more than one definition matches the name.

Keywords coming from libraries are only reported if the library analysis is enabled (it is by default).

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-keyword-prefix.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-keyword-prefix.severity=W"
        ]
        ```

??? example "ignored_sources"

    Comma separated list of the resource files and libraries that do not require the prefix

    **Default value:** BuiltIn

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-keyword-prefix.ignored_sources=BuiltIn
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-keyword-prefix.ignored_sources=BuiltIn"
        ]
        ```

## Lengths

Rules for lengths, such as length of the test case or the file.

### LEN01: too-long-keyword

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0501

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' is too long ({keyword_length}/{allowed_length})`

**Documentation**:

Keyword is too long.

Avoid too long keywords for readability and maintainability.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_len` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_len` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-keyword.severity=W"
        ]
        ```

??? example "max_len"

    Number of lines allowed in a keyword

    **Default value:** 40

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-keyword.max_len=40
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-keyword.max_len=40"
        ]
        ```

??? example "ignore_docs"

    Ignore documentation

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-keyword.ignore_docs=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-keyword.ignore_docs=False"
        ]
        ```

---

### LEN02: too-few-calls-in-keyword

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0502

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})`

**Documentation**:

Too few keyword calls in keyword.

Consider if the custom keyword is required at all.

Incorrect code example:

    *** Test Cases ***
    Test
        Thin Wrapper

    *** Keywords ***
    Thin Wrapper
        Other Keyword    ${arg}

Correct code example:

    *** Test Cases ***
    Test
        Other Keyword    ${arg}

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `min_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `min_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-keyword.severity=W"
        ]
        ```

??? example "min_calls"

    Number of keyword calls required in a keyword

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-keyword.min_calls=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-keyword.min_calls=1"
        ]
        ```

---

### LEN03: too-many-calls-in-keyword

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0503

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})`

**Documentation**:

Too many keyword calls in keyword.

Avoid too long keywords for readability and maintainability.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-keyword.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-keyword.severity=W"
        ]
        ```

??? example "max_calls"

    Number of keyword calls allowed in a keyword

    **Default value:** 10

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-keyword.max_calls=10
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-keyword.max_calls=10"
        ]
        ```

---

### LEN04: too-long-test-case

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0504

Fix availability: There is no automatic fix.

**Message**:

`Test case '{test_name}' is too long ({test_length}/{allowed_length})`

**Documentation**:

Test case is too long.

Avoid too long test cases for readability and maintainability.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_len` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_len` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-test-case.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-test-case.severity=W"
        ]
        ```

??? example "max_len"

    Number of lines allowed in a test case

    **Default value:** 20

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-test-case.max_len=20
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-test-case.max_len=20"
        ]
        ```

??? example "ignore_docs"

    Ignore documentation

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-test-case.ignore_docs=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-test-case.ignore_docs=False"
        ]
        ```

??? example "ignore_templated"

    Ignore templated tests

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-test-case.ignore_templated=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-test-case.ignore_templated=False"
        ]
        ```

---

### LEN05: too-few-calls-in-test-case

Added: `v2.4.0`

Supported RF version `All`

Deprecated names: 0528

Fix availability: There is no automatic fix.

**Message**:

`Test case '{test_name}' has too few keywords inside ({keyword_count}/{min_allowed_count})`

**Documentation**:

Too few keyword calls in test cases.

Test without keywords will fail. Add more keywords or set results using ``Fail``, ``Pass Execution`` or
``Skip`` keywords:

    *** Test Cases ***
    Test case
        [Tags]    smoke
        Skip    Test case draft

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-test-case.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-test-case.severity=E"
        ]
        ```

??? example "min_calls"

    Number of keyword calls required in a test case

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-test-case.min_calls=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-test-case.min_calls=1"
        ]
        ```

??? example "ignore_templated"

    Ignore templated tests

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-few-calls-in-test-case.ignore_templated=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-few-calls-in-test-case.ignore_templated=False"
        ]
        ```

---

### LEN06: too-many-calls-in-test-case

Added: `v1.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Test case '{test_name}' has too many keywords inside ({keyword_count}/{max_allowed_count})`

**Documentation**:

Too many keyword calls in test case.

Redesign the test and move complex logic to separate keywords to increase readability.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-test-case.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-test-case.severity=W"
        ]
        ```

??? example "max_calls"

    Number of keyword calls allowed in a test case

    **Default value:** 10

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-test-case.max_calls=10
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-test-case.max_calls=10"
        ]
        ```

??? example "ignore_templated"

    Ignore templated tests

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-calls-in-test-case.ignore_templated=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-calls-in-test-case.ignore_templated=False"
        ]
        ```

---

### LEN07: too-many-arguments

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0507

Fix availability: There is no automatic fix.

**Message**:

`Keyword '{keyword_name}' has too many arguments ({arguments_count}/{max_allowed_count})`

**Documentation**:

Keyword has too many arguments.

**Style guide**:

- [#arguments](https://docs.robotframework.org/docs/style_guide#arguments)

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_args` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_args` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-arguments.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-arguments.severity=W"
        ]
        ```

??? example "max_args"

    Number of lines allowed in a file

    **Default value:** 5

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-arguments.max_args=5
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-arguments.max_args=5"
        ]
        ```

---

### LEN08: line-too-long

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0508

Fix availability: There is no automatic fix.

**Message**:

`Line is too long ({line_length}/{allowed_length})`

**Documentation**:

The line is too long.

Comments with disabler directives (such as ``# robocop: off``) are ignored. Lines that contain URLs are also
ignored.

It is possible to ignore lines that match the regex pattern. Configure it using the following option:

    robocop check --configure line-too-long.ignore_pattern=pattern

Lines that are part of a documentation (the ``Documentation`` setting or the ``[Documentation]`` setting of a
test case or keyword, together with their ``...`` continuation lines) can be ignored using the following option:

    robocop check --configure line-too-long.ignore_docs=True

This rule is not fixed by ``robocop check --fix``. Use the ``SplitTooLongLine`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#line-length](https://docs.robotframework.org/docs/style_guide#line-length)

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `line_length` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `line_length` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure line-too-long.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "line-too-long.severity=W"
        ]
        ```

??? example "line_length"

    Number of characters allowed in line

    **Default value:** 120

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure line-too-long.line_length=120
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "line-too-long.line_length=120"
        ]
        ```

??? example "ignore_pattern"

    Ignore lines that contain configured pattern

    **Default value:** None

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure line-too-long.ignore_pattern=None
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "line-too-long.ignore_pattern=None"
        ]
        ```

??? example "ignore_docs"

    Ignore lines that are part of a documentation

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure line-too-long.ignore_docs=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "line-too-long.ignore_docs=False"
        ]
        ```

---

### LEN09: empty-section

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0509

Fix availability: Fix is sometimes available.

**Message**:

`Section '{section_name}' is empty`

**Documentation**:

Section is empty.

Empty section does not have any effect and can be removed.

Incorrect code example:

    *** Variables ***


    *** Test Cases ***
    Test
        Keyword Call

Correct code:

    *** Test Cases ***
    Test
        Keyword Call

Sections that contain only comments are also reported, but they are not removed by the fix -
it is not possible to tell whether such comments are still relevant.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-section.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-section.severity=W"
        ]
        ```

---

### LEN10: number-of-returned-values

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0510

Fix availability: There is no automatic fix.

**Message**:

`Too many return values ({return_count}/{max_allowed_count})`

**Documentation**:

Too many return values.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_returns` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_returns` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure number-of-returned-values.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "number-of-returned-values.severity=W"
        ]
        ```

??? example "max_returns"

    Allowed number of returned values from a keyword

    **Default value:** 4

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure number-of-returned-values.max_returns=4
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "number-of-returned-values.max_returns=4"
        ]
        ```

---

### LEN11: empty-metadata

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0511

Fix availability: Fix is always available.

**Message**:

`Metadata settings does not have any value set`

**Documentation**:

Metadata settings do not have any value set.

Metadata can be defined in the ``*** Settings ***`` section for the whole suite, and - with
Robot Framework 7.5 and newer - also inside a test case using the ``[Metadata]`` setting.

Incorrect code example:

    *** Settings ***
    Metadata

    *** Test Cases ***
    Test
        [Metadata]
        Keyword

Correct code example:

    *** Settings ***
    Metadata    Platform    ${PLATFORM}

    *** Test Cases ***
    Test
        [Metadata]    Owner    Team Robot
        Keyword

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-metadata.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-metadata.severity=W"
        ]
        ```

---

### LEN12: empty-documentation

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0512

Fix availability: Fix is always available.

**Message**:

`Documentation of {block_name} is empty`

**Documentation**:

Documentation is empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-documentation.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-documentation.severity=W"
        ]
        ```

---

### LEN13: empty-force-tags

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0513

Fix availability: Fix is always available.

**Message**:

`Force Tags are empty`

**Documentation**:

Force Tags are empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-force-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-force-tags.severity=W"
        ]
        ```

---

### LEN14: empty-default-tags

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0514

Fix availability: Fix is always available.

**Message**:

`Default Tags are empty`

**Documentation**:

Default Tags are empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-default-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-default-tags.severity=W"
        ]
        ```

---

### LEN15: empty-variables-import

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0515

Fix availability: Fix is always available.

**Message**:

`Import variables path is empty`

**Documentation**:

Import variables path is empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-variables-import.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-variables-import.severity=E"
        ]
        ```

---

### LEN16: empty-resource-import

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0516

Fix availability: Fix is always available.

**Message**:

`Import resource path is empty`

**Documentation**:

Import resources path is empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-resource-import.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-resource-import.severity=E"
        ]
        ```

---

### LEN17: empty-library-import

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0517

Fix availability: Fix is always available.

**Message**:

`Import library path is empty`

**Documentation**:

Import library path is empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-library-import.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-library-import.severity=E"
        ]
        ```

---

### LEN18: empty-setup

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0518

Fix availability: Fix is always available.

**Message**:

`Setup of {block_name} does not have any keywords`

**Documentation**:

Empty setup.

``[Setup]`` without a value does not have any effect and can be removed.
If the intention is to overwrite the ``Test Setup`` from the settings section, use the explicit ``NONE`` value:

    *** Settings ***
    Test Setup    Open Application

    *** Test Cases ***
    Test without setup
        [Setup]    NONE
        Keyword Call

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-setup.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-setup.severity=W"
        ]
        ```

---

### LEN19: empty-suite-setup

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0519

Fix availability: Fix is always available.

**Message**:

`Suite Setup does not have any keywords`

**Documentation**:

Empty Suite Setup.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-suite-setup.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-suite-setup.severity=W"
        ]
        ```

---

### LEN20: empty-test-setup

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0520

Fix availability: Fix is always available.

**Message**:

`Test Setup does not have any keywords`

**Documentation**:

Empty Test Setup.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-test-setup.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-test-setup.severity=W"
        ]
        ```

---

### LEN21: empty-teardown

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0521

Fix availability: Fix is always available.

**Message**:

`Teardown of {block_name} does not have any keywords`

**Documentation**:

Empty Teardown.

``[Teardown]`` without a value does not have any effect and can be removed.
If the intention is to overwrite the ``Test Teardown`` from the settings section, use the explicit ``NONE`` value:

    *** Settings ***
    Test Teardown    Close Application

    *** Test Cases ***
    Test without teardown
        [Teardown]    NONE
        Keyword Call

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-teardown.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-teardown.severity=E"
        ]
        ```

---

### LEN22: empty-suite-teardown

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0522

Fix availability: Fix is always available.

**Message**:

`Suite Teardown does not have any keywords`

**Documentation**:

Empty Suite Teardown.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-suite-teardown.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-suite-teardown.severity=W"
        ]
        ```

---

### LEN23: empty-test-teardown

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0523

Fix availability: Fix is always available.

**Message**:

`Test Teardown does not have any keywords`

**Documentation**:

Empty Test Teardown.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-test-teardown.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-test-teardown.severity=W"
        ]
        ```

---

### LEN24: empty-timeout

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0524

Fix availability: Fix is always available.

**Message**:

`Timeout of {block_name} is empty`

**Documentation**:

Empty Timeout.

``[Timeout]`` without a value does not have any effect and can be removed.
If the intention is to overwrite the ``Test Timeout`` from the settings section, use the explicit ``NONE`` value:

    *** Settings ***
    Test Timeout    1 min

    *** Test Cases ***
    Test without timeout
        [Timeout]    NONE
        Keyword Call

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-timeout.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-timeout.severity=W"
        ]
        ```

---

### LEN25: empty-test-timeout

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0525

Fix availability: Fix is always available.

**Message**:

`Test Timeout is empty`

**Documentation**:

Empty Test Timeout.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-test-timeout.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-test-timeout.severity=W"
        ]
        ```

---

### LEN26: empty-arguments

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0526

Fix availability: Fix is always available.

**Message**:

`Arguments of {block_name} are empty`

**Documentation**:

Empty ``[Arguments]`` setting.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-arguments.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-arguments.severity=W"
        ]
        ```

---

### LEN27: too-many-test-cases

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0527

Fix availability: There is no automatic fix.

**Message**:

`Too many test cases ({test_count}/{max_allowed_count})`

**Documentation**:

Too many test cases.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_testcases or max_templated_testcases` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_testcases or max_templated_testcases` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-test-cases.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-test-cases.severity=W"
        ]
        ```

??? example "max_testcases"

    Number of test cases allowed in a suite

    **Default value:** 50

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-test-cases.max_testcases=50
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-test-cases.max_testcases=50"
        ]
        ```

??? example "max_templated_testcases"

    Number of test cases allowed in a templated suite

    **Default value:** 100

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-test-cases.max_templated_testcases=100
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-test-cases.max_templated_testcases=100"
        ]
        ```

---

### LEN28: file-too-long

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0506

Fix availability: There is no automatic fix.

**Message**:

`File has too many lines ({lines_count}/{max_allowed_count})`

**Documentation**:

File has too many lines.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_lines` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_lines` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure file-too-long.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "file-too-long.severity=W"
        ]
        ```

??? example "max_lines"

    Number of lines allowed in a file

    **Default value:** 400

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure file-too-long.max_lines=400
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "file-too-long.max_lines=400"
        ]
        ```

---

### LEN29: empty-test-template

Added: `v3.1.0`

Supported RF version `All`

Fix availability: Fix is always available.

**Message**:

`Test Template is empty`

**Documentation**:

Test Template is empty.

``Test Template`` sets the template to all tests in a suite. Empty value is considered an error
because it leads the users to wrong impression on how the suite operates.
Without value, the setting is ignored and the tests are not templated.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-test-template.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-test-template.severity=W"
        ]
        ```

---

### LEN30: empty-template

Added: `v3.1.0`

Supported RF version `All`

Deprecated names: 0530

Fix availability: Fix is always available.

**Message**:

`Template of {block_name} is empty. To overwrite suite Test Template use more explicit [Template]  NONE`

**Documentation**:

``[Template]`` is empty.

The ``[Template]`` setting overrides the possible template set in the Setting section, and an empty value for
``[Template]`` means that the test has no template even when Test Template is used.

If it is intended behavior, use a more explicit `` NONE `` value to indicate that you want to overwrite suite
Test Template:

    *** Settings ***
    Test Template    Template Keyword

    *** Test Cases ***
    Templated test
        argument

    Not templated test
        [Template]    NONE

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-template.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-template.severity=W"
        ]
        ```

---

### LEN31: empty-keyword-tags

Added: `v3.3.0`

Supported RF version `>=6`

Deprecated names: 0531

Fix availability: Fix is always available.

**Message**:

`Keyword Tags are empty`

**Documentation**:

Keyword Tags are empty.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-keyword-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-keyword-tags.severity=W"
        ]
        ```

---

### LEN32: too-long-variable-name

Added: `v6.7.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Variable name '{variable_name}' is too long ({variable_name_length}/{allowed_length})`

**Documentation**:

Variable name is too long.

Avoid too long variable names for readability and maintainability.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_len` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_len` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-variable-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-variable-name.severity=W"
        ]
        ```

??? example "max_len"

    Allowed length of a variable name

    **Default value:** 40

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-long-variable-name.max_len=40
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-long-variable-name.max_len=40"
        ]
        ```

---

### LEN33: metadata-without-value

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Metadata '{metadata_name}' does not have a value`

**Documentation**:

Metadata name is defined without a value.

Metadata with only a name is recorded with an empty value, which is rarely intended and shows up as
an empty entry in the report and log. Provide a value, or remove the metadata altogether.

Metadata can be defined in the ``*** Settings ***`` section for the whole suite, and - with
Robot Framework 7.5 and newer - also inside a test case using the ``[Metadata]`` setting.

Incorrect code example:

    *** Settings ***
    Metadata    Platform

    *** Test Cases ***
    Test
        [Metadata]    Owner
        Keyword

Correct code example:

    *** Settings ***
    Metadata    Platform    ${PLATFORM}

    *** Test Cases ***
    Test
        [Metadata]    Owner    Team Robot
        Keyword

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure metadata-without-value.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "metadata-without-value.severity=W"
        ]
        ```

## Miscellaneous

Miscellaneous rules.

### MISC01: keyword-after-return

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0901

Fix availability: There is no automatic fix.

**Message**:

`{error_msg}`

**Documentation**:

Keyword call after the `` [Return]`` setting.

To improve readability, use ``[Return]`` setting at the end of the keyword. If you want to return immediately
from the keyword, use the ``RETURN`` statement instead. ``[Return]`` does not return from the keyword but only
sets the values that will be returned at the end of the keyword.

Incorrect code example:

    *** Keywords ***
    Keyword
        Step
        [Return]    ${variable}
        ${variable}    Other Step

Correct code:

    *** Keywords ***
    Keyword
        Step
        ${variable}    Other Step
        [Return]    ${variable}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-after-return.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-after-return.severity=W"
        ]
        ```

---

### MISC02: empty-return

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0903

Fix availability: Fix is always available.

**Message**:

`[Return] is empty`

**Documentation**:

``[Return]`` is empty.

``[Return]`` statement is used to define variables returned from keyword. If you don't return anything from
a keyword, don't use ``[Return]``.

Incorrect code example:

    *** Keywords ***
    Keyword
        Gather Results
        Assert Results
        [Return]

Correct code:

    *** Keywords ***
    Keyword
        Gather Results
        Assert Results

The fix removes the empty ``[Return]`` setting. Comments are not removed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-return.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-return.severity=W"
        ]
        ```

---

### MISC03: nested-for-loop

Added: `v1.0.0`

Supported RF version `<4.0`

Deprecated names: 0907

Fix availability: There is no automatic fix.

**Message**:

`Not supported nested for loop`

**Documentation**:

Not supported nested for loop.

Older versions of Robot Framework did not support nested for loops:

    *** Test Cases
    Test case
        FOR    ${var}    IN RANGE    10
            FOR   ${other_var}   IN    a  b
                # Nesting supported from Robot Framework 4.0+
            END
        END

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure nested-for-loop.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "nested-for-loop.severity=E"
        ]
        ```

---

### MISC04: inconsistent-assignment

Added: `v1.7.0`

Supported RF version `All`

Deprecated names: 0909

Fix availability: Fix is always available.

**Message**:

`The assignment sign is not consistent within the file. Expected '{expected_sign}' but got '{actual_sign}' instead`

**Documentation**:

Not consistent assignment sign in the file.

Use only one type of assignment sign in a file. Assignment signs are checked in the keyword calls and in the
``VAR`` syntax (Robot Framework 7 and newer). The ``*** Variables ***`` section is handled by the
``inconsistent-assignment-in-variables`` rule.

Incorrect code example:

    *** Keywords ***
    Keyword
        ${var} =  Other Keyword
        No Operation

    Keyword 2
        No Operation
        ${var}  ${var2}    Some Keyword

Correct code:

    *** Keywords ***
    Keyword
        ${var}    Other Keyword
        No Operation

    Keyword 2
        No Operation
        ${var}  ${var2}    Some Keyword

By default, Robocop looks for the most popular assignment sign in the file. It is possible to define the expected
assignment sign:

=== ":octicons-command-palette-24: cli"

```bash
robocop check --configure inconsistent-assignment.assignment_sign_type=none
```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    configure = [
        "inconsistent-assignment.assignment_sign_type=none"
    ]
    ```

You can choose between the following assignment signs:

- 'autodetect' (default),
- 'none',
- 'equal_sign' (``=``)
- 'space_and_equal_sign' (`` =``).

The assignment sign can be replaced with the expected one automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inconsistent-assignment.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-assignment.severity=W"
        ]
        ```

??? example "assignment_sign_type"

    Possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or space_and_equal_sign (' =')

    **Default value:** autodetect

    **Type:** assignment sign type

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inconsistent-assignment.assignment_sign_type=autodetect
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-assignment.assignment_sign_type=autodetect"
        ]
        ```

---

### MISC05: inconsistent-assignment-in-variables

Added: `v1.7.0`

Supported RF version `All`

Deprecated names: 0910

Fix availability: Fix is always available.

**Message**:

`The assignment sign is not consistent inside the variables section. Expected '{expected_sign}' but got '{actual_sign}' instead`

**Documentation**:

Not consistent assignment sign in the ``*** Variables ***`` section.

Use one type of assignment sign in the Variables section.

Incorrect code example:

    *** Variables ***
    ${var} =    1
    ${var2}=    2
    ${var3} =   3
    ${var4}     a
    ${var5}     b

Correct code:

    *** Variables ***
    ${var}      1
    ${var2}     2
    ${var3}     3
    ${var4}     a
    ${var5}     b

By default, Robocop looks for the most popular assignment sign in the file. It is possible to define the expected
assignment sign by running:

    robocop check --configure inconsistent-assignment-in-variables.assignment_sign_type=equal_sign

You can choose between the following signs:

- 'autodetect' (default),
- 'none',
- 'equal_sign' (``=``)
- 'space_and_equal_sign' (`` =``).

The assignment sign can be replaced with the expected one automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inconsistent-assignment-in-variables.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-assignment-in-variables.severity=W"
        ]
        ```

??? example "assignment_sign_type"

    Possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') or space_and_equal_sign (' =')

    **Default value:** autodetect

    **Type:** assignment sign type

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inconsistent-assignment-in-variables.assignment_sign_type=autodetect
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-assignment-in-variables.assignment_sign_type=autodetect"
        ]
        ```

---

### MISC06: can-be-resource-file

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0913

Fix availability: There is no automatic fix.

**Message**:

`No tests in '{file_name}' file, consider renaming to '{file_name_stem}.resource'`

**Documentation**:

No tests in the file, consider renaming the file extension to ``.resource``.

If the Robot file contains only keywords or variables, it's a good practice to use ``.resource`` extension.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure can-be-resource-file.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "can-be-resource-file.severity=I"
        ]
        ```

---

### MISC07: if-can-be-merged

Added: `v2.0.0`

Supported RF version `>=4.0`

Deprecated names: 0914

Fix availability: There is no automatic fix.

**Message**:

`IF statement can be merged with previous IF (defined in line {line})`

**Documentation**:

IF statement can be merged with the previous IF.

``IF`` statement follows another ``IF`` with identical conditions. It can be possibly merged into one.

Example of rule violation:

    *** Test Cases ***
    Test case
        IF  ${var} == 4
            Keyword
        END
        # comments are ignored
        IF  ${var}  == 4
            Keyword 2
        END

``IF`` statement is considered identical only if all branches have identical conditions.

Similar but not identical ``IF``:

    *** Test Cases ***
    Test case
        IF  ${variable}
            Keyword
        ELSE
            Other Keyword
        END
        IF  ${variable}
            Keyword
        END

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure if-can-be-merged.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "if-can-be-merged.severity=I"
        ]
        ```

---

### MISC08: statement-outside-loop

Added: `v2.0.0`

Supported RF version `>=5.0`

Deprecated names: 0915

Fix availability: There is no automatic fix.

**Message**:

`{name} {statement_type} used outside a loop`

**Documentation**:

Loop statement used outside loop.

Following keywords and statements should only be used inside loop (``WHILE`` or ``FOR``):
    - ``Exit For Loop``
    - ``Exit For Loop If``
    - ``Continue For Loop``
    - ``Continue For Loop If``
    - ``CONTINUE``
    - ``BREAK``

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure statement-outside-loop.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "statement-outside-loop.severity=E"
        ]
        ```

---

### MISC09: inline-if-can-be-used

Added: `v2.0.0`

Supported RF version `>=5.0`

Deprecated names: 0916

Fix availability: Fix is sometimes available.

**Message**:

`IF can be replaced with inline IF`

**Documentation**:

IF can be replaced with inline IF.

Short and simple ``IF`` statements can be replaced with ``inline IF``.

Following ``IF``:

    IF    $condition
        BREAK
    END

can be replaced with:

    IF    $condition    BREAK

The fix replaces the ``IF`` block with an ``inline IF``.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `max_width` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `max_width` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inline-if-can-be-used.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inline-if-can-be-used.severity=I"
        ]
        ```

??? example "max_width"

    Maximum width of if (in characters) below which it will be recommended to use inline if

    **Default value:** 80

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inline-if-can-be-used.max_width=80
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inline-if-can-be-used.max_width=80"
        ]
        ```

---

### MISC10: unreachable-code

Added: `v3.1.0`

Supported RF version `>=5.0`

Deprecated names: 0917

Fix availability: There is no automatic fix.

**Message**:

`Unreachable code after {statement} statement`

**Documentation**:

Unreachable code.

Detects the unreachable code after ``RETURN``, ``BREAK`` or ``CONTINUE`` statements.

For example:

    *** Keywords ***
    Example Keyword
        FOR    ${animal}    IN    cat    dog
            IF    '${animal}' == 'cat'
                CONTINUE
                Log  ${animal}  # unreachable log
            END
            BREAK
            Log    Unreachable log
        END
        RETURN
        Log    Unreachable log

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unreachable-code.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unreachable-code.severity=W"
        ]
        ```

---

### MISC11: multiline-inline-if

Added: `v3.1.0`

Supported RF version `>=5.0`

Deprecated names: 0918

Fix availability: There is no automatic fix.

**Message**:

`Inline IF split to multiple lines`

**Documentation**:

Multi-line inline IF.

It's allowed to create ``inline IF`` that spans multiple lines, but it should be avoided,
since it decreases readability. Try to use normal ``IF``/``ELSE`` instead.

Incorrect code example:

    *** Keywords ***
    Keyword
        IF  ${condition}  Log  hello
        ...    ELSE       Log  hi!

Correct code:

    *** Keywords ***
    Keyword
        IF  ${condition}    Log  hello     ELSE    Log  hi!

or IF block can be used:

    *** Keywords ***
    Keyword
        IF  ${condition}
            Log  hello
        ELSE
            Log  hi!
        END

Use the ``InlineIf`` formatter (``robocop format``) to reformat the inline IF.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure multiline-inline-if.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "multiline-inline-if.severity=W"
        ]
        ```

---

### MISC12: unnecessary-string-conversion

> **Warning**
>
> Rule is deprecated.

Added: `v4.0.0`

Supported RF version `>=4.0`

Deprecated names: 0923

Fix availability: There is no automatic fix.

**Message**:

`Variable '{name}' in '{block_name}' condition has unnecessary string conversion`

**Documentation**:

Variable in the condition has unnecessary string conversion.

Expressions in Robot Framework are evaluated using Python's eval function. When a variable is used
in the expression using the normal ``${variable}`` syntax, its value is replaced before the expression
is evaluated. For example, with the following expression:

    *** Test Cases ***
    Check if schema was uploaded
        Upload Schema    schema.avsc
        Check If File Exist In SFTP    schema.avsc

    *** Keywords ***
    Upload Schema
        [Arguments]    ${filename}
        IF    ${filename} == 'default'
            ${filename}    Get Default Upload Path
        END
        Send File To SFTP Root   ${filename}

"${filename}" will be replaced by "schema.avsc":

    IF    schema.avsc == 'default'

"schema.avsc" will not be recognized as Python variable. That's why you need to quote it:

    IF    '${filename}' == 'default'

However, it introduces unnecessary string conversion and can mask difference in the type. For example:

    ${numerical}    Set Variable    10  # ${numerical} is actually string 10, not integer 10
    IF    "${numerical}" == "10"

You can use  ``$variable`` syntax instead:

    IF    $numerical == 10

It will put the actual variable in the evaluated expression without converting it to string.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unnecessary-string-conversion.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unnecessary-string-conversion.severity=I"
        ]
        ```

---

### MISC13: expression-can-be-simplified

Added: `v4.0.0`

Supported RF version `>=4.0`

Deprecated names: 0924

Fix availability: There is no automatic fix.

**Message**:

`'{block_name}' condition can be simplified`

**Documentation**:

Condition can be simplified.

Evaluated expression can be simplified.

Incorrect code example:

    *** Keywords ***
    Click On Element
        [Arguments]    ${locator}
        IF    ${is_element_visible}==${TRUE}    RETURN
        ${is_element_enabled}    Set Variable    ${TRUE}
        WHILE    ${is_element_enabled} != ${TRUE}
            ${is_element_enabled}    Get Element Status    ${locator}
        END
        Click    ${locator}

Correct code:

    *** Keywords ***
    Click On Element
        [Arguments]    ${locator}
        IF    ${is_element_visible}    RETURN
        ${is_element_enabled}    Set Variable    ${FALSE}
        WHILE    not ${is_element_enabled}
            ${is_element_enabled}    Get Element Status    ${locator}
        END
        Click    ${locator}

Comparisons to empty sequences (lists, dicts, sets), empty string or ``0`` can be also simplified:

    *** Test Cases ***
    Check conditions
        Should Be True     ${list} == []  # equivalent of 'not ${list}'
        Should Be True     ${string} != ""  # equivalent of '${string}'
        Should Be True     len(${sequence}))  # equivalent of '${sequence}'

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure expression-can-be-simplified.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "expression-can-be-simplified.severity=I"
        ]
        ```

---

### MISC14: misplaced-negative-condition

Added: `v4.0.0`

Supported RF version `>=4.0`

Deprecated names: 0925

Fix availability: Fix is sometimes available.

**Message**:

`'{block_name}' condition '{original_condition}' can be rewritten to '{proposed_condition}'`

**Documentation**:

The position of not operator can be changed for better readability.

Incorrect code example:

    *** Keywords ***
    Check Unmapped Codes
        ${codes}    Get Codes From API
        IF    not ${codes} is None
            FOR    ${code}    IN    @{codes}
                Validate Single Code    ${code}
            END
        ELSE
            Fail    Did not receive codes from API.
        END

Correct code:

    *** Keywords ***
    Check Unmapped Codes
        ${codes}    Get Codes From API
        IF    ${codes} is not None
            FOR    ${code}    IN    @{codes}
                Validate Single Code    ${code}
            END
        ELSE
            Fail    Did not receive codes from API.
        END

The condition can be rewritten automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure misplaced-negative-condition.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "misplaced-negative-condition.severity=I"
        ]
        ```

---

### MISC15: unused-disabler

Added: `v6.8.0`

Supported RF version `All`

Fix availability: Fix is sometimes available.

**Message**:

`Disabler directive found for '{rule_name}' rule(s) but no violation found`

**Documentation**:

Robocop disabler directive is not used.

Overlapping disablers, code that was already fixed or rules that are disabled globally do not need rule disablers.

Rule violation examples:

    *** Keywords ***
    Log To Page
        ${email}    Get Email  # robocop: off=unused-variable
        Log    ${email}
        FOR    ${locator}    IN    @{email_locators}
            # robocop: off
            # robocop: off=some-rule
            Fill Text    ${locator}
        END

In the above examples we disable unused-variable rule, but no violation is raised for this line.
Also, we define disablers for all rules and some-rule in FOR loop, and all rules disabler overlaps second disabler
which is never used.

Unused disablers can be removed automatically with the ``--fix`` option. Only the unused rule name is removed
if the directive disables more rules. Disablers that share the comment with any other content are not
removed automatically.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-disabler.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-disabler.severity=I"
        ]
        ```

---

### MISC16: not-enough-whitespace-around-operator

Added: `v9.0.0`

Supported RF version `>=4.0`

Fix availability: Fix is always available.

**Message**:

`Not enough whitespace around '{operator}' operator in '{block_name}' condition`

**Documentation**:

Not enough whitespace around a comparison operator.

Comparison operators (``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``) used in conditions are easier to read
when they are surrounded by spaces. The rule inspects conditions of ``IF`` and ``WHILE`` blocks together with
the conditions passed to the BuiltIn keywords that evaluate an expression
(such as ``Should Be True`` or ``Skip If``).

Incorrect code example:

    *** Test Cases ***
    Test
        IF    ${variable}==5
            Log    Robocop
        END
        WHILE    ${counter}>=${LIMIT}
            ${counter}    Evaluate    ${counter} + 1
        END
        Should Be True    ${left}!=${right}

Correct code:

    *** Test Cases ***
    Test
        IF    ${variable} == 5
            Log    Robocop
        END
        WHILE    ${counter} >= ${LIMIT}
            ${counter}    Evaluate    ${counter} + 1
        END
        Should Be True    ${left} != ${right}

The missing whitespace can be added automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-enough-whitespace-around-operator.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-enough-whitespace-around-operator.severity=I"
        ]
        ```

## Naming

Naming rules.

### NAME01: not-allowed-char-in-name

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0301

Fix availability: There is no automatic fix.

**Message**:

`Not allowed character '{character}' found in {block_name} name`

**Documentation**:

Not allowed character found.

Reports not allowed characters found in Test Case or Keyword names. By default, it's a dot (``.``). You can
configure what patterns are reported by calling:

    robocop check --configure not-allowed-char-in-name.pattern=regex_pattern

``regex_pattern`` should define a regex pattern not allowed in names. For example, ``[@\[]`` pattern
would report any occurrence of ``@[`` characters.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-char-in-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-char-in-name.severity=W"
        ]
        ```

??? example "pattern"

    Pattern defining characters (not) allowed in a name

    **Default value:** re.compile('[\\.\\?]')

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-char-in-name.pattern=re.compile('[\\.\\?]')
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-char-in-name.pattern=re.compile('[\\.\\?]')"
        ]
        ```

---

### NAME02: wrong-case-in-keyword-name

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0302

Fix availability: Fix is sometimes available.

**Message**:

`Keyword name '{keyword_name}' does not follow case convention`

**Documentation**:

Keyword name does not follow case convention.

Keyword names need to follow a specific case convention.
The convention can be set using the `` convention `` parameter and accepts
one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such
convention:

    *** Keywords ***
    Fill Out The Form
        Provide Shipping Address
        Provide Payment Method
        Click 'Next' Button
        [Teardown]  Log Form Data

You can also set it to ``first_word_capitalized`` which requires capitalising the first word of the keyword:

    *** Keywords ***
    Fill out the form
        Provide shipping address
        Provide payment method
        Click 'Next' button
        [Teardown]  Log form data

The rule also accepts another parameter ``pattern`` which can be used to configure words
that are accepted in the keyword name, even though they violate the case convention.

``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\.readthedocs\.io``
would make the following keyword legal:

    Go To robocop.readthedocs.io Page

See the sibling rule [wrong-case-in-keyword-call](#name18-wrong-case-in-keyword-call) that checks keyword call
naming convention.

Keyword names are case-insensitive in Robot Framework, so the name can be capitalized automatically with the
``--fix`` option. Names matching the configured ``pattern`` are reported, but not fixed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-name.severity=W"
        ]
        ```

??? example "convention"

    Possible values: 'each_word_capitalized' (default) or 'first_word_capitalized'

    **Default value:** each_word_capitalized

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-name.convention=each_word_capitalized
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-name.convention=each_word_capitalized"
        ]
        ```

??? example "pattern"

    Pattern for accepted words in keyword

    **Default value:** re.compile('')

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-name.pattern=re.compile('')
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-name.pattern=re.compile('')"
        ]
        ```

---

### NAME03: keyword-name-is-reserved-word

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0303

Fix availability: There is no automatic fix.

**Message**:

`'{keyword_name}' is a reserved keyword{error_msg}`

**Documentation**:

Keyword name is a reserved word.

Do not use reserved names for keyword names. The following names are reserved:

  - IF
  - ELSE IF
  - ELSE
  - FOR
  - END
  - WHILE
  - CONTINUE
  - RETURN
  - TRY
  - EXCEPT
  - FINALLY

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-name-is-reserved-word.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-name-is-reserved-word.severity=W"
        ]
        ```

---

### NAME04: underscore-in-keyword-name

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0305

Fix availability: There is no automatic fix.

**Message**:

`Underscores in keyword name '{keyword_name}'`

**Documentation**:

Underscores in keyword name.

You can replace underscores with spaces.

Incorrect code example:

    keyword_with_underscores

Correct code:

    Keyword Without Underscores

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure underscore-in-keyword-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "underscore-in-keyword-name.severity=W"
        ]
        ```

---

### NAME05: setting-name-not-in-title-case

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0306

Fix availability: Fix is always available.

**Message**:

`Setting name '{setting_name}' not in title or uppercase`

**Documentation**:

Setting name not in the title or upper case.

Incorrect code example:

    *** Settings ***
    resource    file.resource

    *** Test Cases ***
    Test
        [documentation]  Some documentation
        Step

Correct code:

    *** Settings ***
    Resource    file.resource

    *** Test Cases ***
    Test
        [DOCUMENTATION]  Some documentation
        Step

The setting name can be converted to the title case automatically with the ``--fix`` option.
Use the ``NormalizeSettingName`` formatter (``robocop format``) if you also want to normalize
the whitespace inside the setting name.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure setting-name-not-in-title-case.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "setting-name-not-in-title-case.severity=W"
        ]
        ```

---

### NAME06: section-name-invalid

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0307

Fix availability: Fix is always available.

**Message**:

`Section name should be in format '{section_title_case}' or '{section_upper_case}'`

**Documentation**:

Section name does not follow convention.

Section name should use Title Case or CAP CASE case convention.

Incorrect code example:

    *** settings ***
    *** KEYwords ***

Correct code:

    *** SETTINGS ***
    *** Keywords ***

The section name can be replaced with its title case version automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure section-name-invalid.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "section-name-invalid.severity=W"
        ]
        ```

---

### NAME07: not-capitalized-test-case-title

Added: `v1.4.0`

Supported RF version `All`

Deprecated names: 0308

Fix availability: There is no automatic fix.

**Message**:

`Test case '{test_name}' title does not start with capital letter`

**Documentation**:

Test case title does not start with a capital letter.

Incorrect code example:

    *** Test Cases ***
    validate user details

Correct code example:

    *** Test Cases ***
    Validate user details

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-capitalized-test-case-title.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-capitalized-test-case-title.severity=W"
        ]
        ```

---

### NAME08: section-variable-not-uppercase

Added: `v1.4.0`

Supported RF version `All`

Deprecated names: 0309

Fix availability: There is no automatic fix.

**Message**:

`Section variable '{variable_name}' name is not uppercase`

**Documentation**:

Section variable name is not uppercase.

Incorrect code example:

    *** Variables ***
    ${section_variable}    value

Correct code:

    *** Variables ***
    ${SECTION_VARIABLE}    value

**Style guide**:

- [#variables-section](https://docs.robotframework.org/docs/style_guide#variables-section)
- [#variable-scope-and-casing](https://docs.robotframework.org/docs/style_guide#variable-scope-and-casing)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure section-variable-not-uppercase.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "section-variable-not-uppercase.severity=W"
        ]
        ```

---

### NAME09: else-not-upper-case

Added: `v1.5.0`

Supported RF version `All`

Deprecated names: 0311

Fix availability: Fix is always available.

**Message**:

`ELSE and ELSE IF is not uppercase`

**Documentation**:

ELSE and ELSE IF is not uppercase.

Incorrect code example:

    *** Keywords ***
    Describe Temperature
        [Arguments]     ${degrees}
        If         ${degrees} > ${30}
            RETURN  Hot
        else if    ${degrees} > ${15}
            RETURN  Warm
        Else
            RETURN  Cold

Correct code:

    *** Keywords ***
    Describe Temperature
        [Arguments]     ${degrees}
        IF         ${degrees} > ${30}
            RETURN  Hot
        ELSE IF    ${degrees} > ${15}
            RETURN  Warm
        ELSE
            RETURN  Cold

The fix replaces the ``ELSE`` and ``ELSE IF`` names with their uppercase versions.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure else-not-upper-case.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "else-not-upper-case.severity=E"
        ]
        ```

---

### NAME10: keyword-name-is-empty

Added: `v1.8.0`

Supported RF version `All`

Deprecated names: 0312

Fix availability: There is no automatic fix.

**Message**:

`Keyword name is empty`

**Documentation**:

Keyword name is empty.

Remember to always add a keyword name and avoid such code:

    *** Keywords ***
    # no keyword name here!!!
        Log To Console  hi

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-name-is-empty.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-name-is-empty.severity=E"
        ]
        ```

---

### NAME11: test-case-name-is-empty

Added: `v1.8.0`

Supported RF version `All`

Deprecated names: 0313

Fix availability: There is no automatic fix.

**Message**:

`Test case name is empty`

**Documentation**:

Test case name is empty.

Remember to always add a test case name and avoid such code:

    *** Test Cases ***
    # no test case name here!!!
        Log To Console  hello

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure test-case-name-is-empty.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "test-case-name-is-empty.severity=E"
        ]
        ```

---

### NAME12: empty-library-alias

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0314

Fix availability: Fix is sometimes available.

**Message**:

`Library alias is empty`

**Documentation**:

Library alias is empty.

Use a non-empty name when using library import with alias.

Incorrect code example:

     *** Settings ***
     Library  CustomLibrary  AS

Correct code:

    *** Settings ***
    Library  CustomLibrary  AS  AnotherName

The fix removes the alias marker without the name. Imports with the alias split into multiple lines
are not fixed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-library-alias.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-library-alias.severity=W"
        ]
        ```

---

### NAME13: duplicated-library-alias

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0315

Fix availability: Fix is sometimes available.

**Message**:

`Library alias is the same as original name`

**Documentation**:

Library alias is the same as the original name.

Examples of rule violation:

     *** Settings ***
     Library  CustomLibrary  AS  CustomLibrary   # same as library name
     Library  CustomLibrary  AS  Custom Library  # same as library name (spaces are ignored)

The fix removes the redundant alias. Imports with the alias split into multiple lines are not fixed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-library-alias.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-library-alias.severity=W"
        ]
        ```

---

### NAME14: bdd-without-keyword-call

Added: `v1.11.0`

Supported RF version `All`

Deprecated names: 0318

Fix availability: There is no automatic fix.

**Message**:

`BDD reserved keyword '{keyword_name}' not followed by any keyword{error_msg}`

**Documentation**:

BDD keyword isn't followed by any keyword.

When using BDD reserved keywords (such as `GIVEN`, `WHEN`, `AND`, `BUT` or `THEN`) use them together with
the name of the keyword to run.

Incorrect code example:

    *** Test Cases ***
    Test case
        Given
        When User Log In
        Then User Should See Welcome Page

Correct code:

    *** Test Cases ***
    Test case
        Given Setup Is Complete
        When User Log In
        Then User Should See Welcome Page

Since those words are used for BDD style, it's also recommended not to use them within the user keyword name.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure bdd-without-keyword-call.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "bdd-without-keyword-call.severity=W"
        ]
        ```

---

### NAME15: not-allowed-char-in-filename

Added: `v2.1.0`

Supported RF version `All`

Deprecated names: 0320

Fix availability: There is no automatic fix.

**Message**:

`Not allowed character '{character}' found in {block_name} name`

**Documentation**:

Not allowed character found in filename.

Reports not allowed pattern found in Suite names. By default, it's a dot (`.`).
You can configure what characters are reported by running:

     robocop check --configure not-allowed-char-in-filename.pattern=regex_pattern .

where ``regex_pattern`` should define regex pattern for characters not allowed in names. For example `[@\[]`
pattern would report any occurrence of ``@[`` characters.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-char-in-filename.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-char-in-filename.severity=W"
        ]
        ```

??? example "pattern"

    Pattern defining characters (not) allowed in a name

    **Default value:** re.compile('[\\.\\?]')

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-allowed-char-in-filename.pattern=re.compile('[\\.\\?]')
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-allowed-char-in-filename.pattern=re.compile('[\\.\\?]')"
        ]
        ```

---

### NAME16: invalid-section

Added: `v3.2.0`

Supported RF version `>=6.1`

Deprecated names: 0325

Fix availability: There is no automatic fix.

**Message**:

`Invalid section '{invalid_section}'`

**Documentation**:

Invalid section found.

Robot Framework 6.1 detects unrecognized sections based on the language defined for the specific files.
Consider using the `` -- language `` parameter if the file is defined with a different language.

It is also possible to configure language in the file:

    language: pl

    *** Przypadki Testowe ***
    Wypisz dyrektywę 4
        Log   Błąd dostępu

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure invalid-section.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "invalid-section.severity=E"
        ]
        ```

---

### NAME17: mixed-task-test-settings

Added: `v3.3.0`

Supported RF version `All`

Deprecated names: 0326

Fix availability: There is no automatic fix.

**Message**:

`Use {task_or_test}-related setting '{setting}' if {tasks_or_tests} section is used`

**Documentation**:

Task related setting used with ``*** Test Cases ***`` or Test related setting used with the `` *** Tasks ***``
section.

If the `` *** Tasks ***`` section is present in the file, use task-related settings like ``Task Setup``,
``Task Teardown``, ``Task Template``, ``Task Tags`` and ``Task Timeout`` instead of their `Test` variants.

Similarly, use test-related settings when using the `` *** Test Cases ***`` section.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure mixed-task-test-settings.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "mixed-task-test-settings.severity=W"
        ]
        ```

---

### NAME18: wrong-case-in-keyword-call

Added: `v7.0.0`

Supported RF version `All`

Fix availability: Fix is sometimes available.

**Message**:

`Keyword name '{keyword_name}' does not follow case convention`

**Documentation**:

Keyword call name does not follow case convention.

Keyword names need to follow a specific case convention.
The convention can be set using the `` convention `` parameter and accepts
one of the 2 values: ``each_word_capitalized`` or ``first_word_capitalized``.

By default, it's configured to ``each_word_capitalized``, which requires each keyword to follow such
convention:

    *** Keywords ***
    Fill out the form
        Provide Shipping Address
        Provide Payment Method
        Click 'Next' Button
        [Teardown]  Log Form Data

You can also set it to ``first_word_capitalized`` which requires capitalising the first word of the keyword:

    *** Keywords ***
    Fill out the form
        Provide shipping address
        Provide payment method
        Click 'Next' button
        [Teardown]  Log form data

The rule also accepts another parameter ``pattern`` which can be used to configure words
that are accepted in the keyword name, even though they violate the case convention.

``pattern`` parameter accepts a regex pattern. For example, configuring it to ``robocop\.readthedocs\.io``
would make the following keyword legal:

    Go To robocop.readthedocs.io Page

See the sibling rule [wrong-case-in-keyword-name](#name02-wrong-case-in-keyword-name) that checks keyword definition
naming convention.

Keyword names are case-insensitive in Robot Framework, so the name can be capitalized automatically with the
``--fix`` option. The optional library name prefix is not modified. Names matching the configured ``pattern``
are reported, but not fixed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-call.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-call.severity=W"
        ]
        ```

??? example "convention"

    Possible values: 'each_word_capitalized' (default) or 'first_word_capitalized'

    **Default value:** each_word_capitalized

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-call.convention=each_word_capitalized
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-call.convention=each_word_capitalized"
        ]
        ```

??? example "pattern"

    Pattern for accepted words in keyword

    **Default value:** re.compile('')

    **Type:** regex

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure wrong-case-in-keyword-call.pattern=re.compile('')
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "wrong-case-in-keyword-call.pattern=re.compile('')"
        ]
        ```

## Order

Ordering rules.

### ORD01: test-case-section-out-of-order

Added: `v5.3.0`

Supported RF version `All`

Deprecated names: 0927

Fix availability: There is no automatic fix.

**Message**:

`'{section_name}' is in wrong place of Test Case. Recommended order of elements in Test Cases: {recommended_order}`

**Documentation**:

Settings or body in the test case are out of order.

Sections should be defined in order set by the ``sections_order`` parameter.
Default order: ``documentation,metadata,tags,timeout,setup,template,keyword,teardown``.

To change the default order, use the following option:

    robocop check --configure test-case-section-out-of-order.sections_order=comma,separated,list,of,sections

where section should be a case-insensitive name from the list:

- documentation
- metadata
- tags
- timeout
- setup
- template
- keyword
- teardown

Order of not configured sections is ignored.

``metadata`` refers to the test case ``[Metadata]`` setting, which requires Robot Framework 7.5 or newer.

Incorrect code example:

    *** Test Cases ***
    Keyword After Teardown
        [Documentation]    This is test Documentation
        [Tags]    tag1    tag2
        [Teardown]    Log    abc
        Keyword1

Correct code:

    *** Test Cases ***
    Keyword After Teardown
        [Documentation]    This is test Documentation
        [Tags]    tag1    tag2
        Keyword1
        [Teardown]    Log    abc

**Style guide**:

- [#test-cases-or-tasks](https://docs.robotframework.org/docs/style_guide#test-cases-or-tasks)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure test-case-section-out-of-order.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "test-case-section-out-of-order.severity=W"
        ]
        ```

??? example "sections_order"

    Order of sections in comma-separated list

    **Default value:** documentation,metadata,tags,timeout,setup,template,keyword,teardown

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure test-case-section-out-of-order.sections_order=documentation,metadata,tags,timeout,setup,template,keyword,teardown
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "test-case-section-out-of-order.sections_order=documentation,metadata,tags,timeout,setup,template,keyword,teardown"
        ]
        ```

---

### ORD02: keyword-section-out-of-order

Added: `v5.3.0`

Supported RF version `All`

Deprecated names: 0928

Fix availability: There is no automatic fix.

**Message**:

`'{section_name}' is in wrong place of Keyword. Recommended order of elements in Keyword: {recommended_order}`

**Documentation**:

Settings or body in keyword are out of order.

Sections should be defined in order set by the ``sections_order`` parameter.
Default order: ``documentation,tags,arguments,timeout,setup,keyword,teardown``.

To change the default order use following option:

    robocop check --configure keyword-section-out-of-order.sections_order=comma,separated,list,of,sections

where section should be case-insensitive name from the list:
documentation, tags, arguments, timeout, setup, keyword, teardown.
Order of not configured sections is ignored.

Incorrect code example:

    *** Keywords ***
    Keyword After Teardown
        [Tags]    tag1    tag2
        [Teardown]    Log    abc
        Keyword1
        [Documentation]    This is keyword Documentation

Correct code example:

    *** Keywords ***
    Keyword After Teardown
        [Documentation]    This is keyword Documentation
        [Tags]    tag1    tag2
        Keyword1
        [Teardown]    Log    abc

**Style guide**:

- [#keyword](https://docs.robotframework.org/docs/style_guide#keyword)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-section-out-of-order.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-section-out-of-order.severity=W"
        ]
        ```

??? example "sections_order"

    Order of sections in comma-separated list

    **Default value:** documentation,tags,arguments,timeout,setup,keyword,teardown

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure keyword-section-out-of-order.sections_order=documentation,tags,arguments,timeout,setup,keyword,teardown
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "keyword-section-out-of-order.sections_order=documentation,tags,arguments,timeout,setup,keyword,teardown"
        ]
        ```

---

### ORD03: section-out-of-order

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0809

Fix availability: There is no automatic fix.

**Message**:

`'{section_name}' section header is defined in wrong order: {recommended_order}`

**Documentation**:

Section does not follow the recommended order.

It's advised to use consistent section orders for readability.

Default order: ``comments,settings,variables,testcases,keywords``.

To change the default order, use the following option:

    robocop check --configure section-out-of-order.sections_order=comma,separated,list,of,sections

The order of not configured sections is ignored.

Incorrect code example:

    *** Settings ***

    *** Keywords ***

    *** Test Cases ***

Correct code:

    *** Settings ***

    *** Test Cases ***

    *** Keywords ***

**Style guide**:

- [#sections](https://docs.robotframework.org/docs/style_guide#sections)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure section-out-of-order.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "section-out-of-order.severity=W"
        ]
        ```

??? example "sections_order"

    Order of sections in comma-separated list

    **Default value:** settings,variables,testcases,keywords

    **Type:** str

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure section-out-of-order.sections_order=settings,variables,testcases,keywords
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "section-out-of-order.sections_order=settings,variables,testcases,keywords"
        ]
        ```

## Spacing

Spacing and whitespace related rules.

### SPC01: trailing-whitespace

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 1001

Fix availability: Fix is always available.

**Message**:

`Trailing whitespace at the end of line`

**Documentation**:

Trailing whitespace at the end of the line.

Invisible, unnecessary whitespace can be confusing.

Incorrect code example:

    *** Keywords ***  \n
    Validate Result\n
    [Arguments]    ${variable}\n
        Should Be True    ${variable}    \n

Correct code:

    *** Keywords ***\n
    Validate Result\n
    [Arguments]    ${variable}\n
        Should Be True    ${variable}\n

**Style guide**:

- [#trailing-whitespaces](https://docs.robotframework.org/docs/style_guide#trailing-whitespaces)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure trailing-whitespace.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "trailing-whitespace.severity=W"
        ]
        ```

---

### SPC02: missing-trailing-blank-line

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 1002

Fix availability: There is no automatic fix.

**Message**:

`Missing trailing blank line at the end of file`

**Documentation**:

Missing trailing blank line at the end of file.

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-sections](https://docs.robotframework.org/docs/style_guide#spacing-after-sections)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-trailing-blank-line.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-trailing-blank-line.severity=W"
        ]
        ```

---

### SPC03: empty-lines-between-sections

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 1003

Fix availability: There is no automatic fix.

**Message**:

`Invalid number of empty lines between sections ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Invalid number of empty lines between sections.

Ensure there is the same number of empty lines between sections for consistency and readability.

Incorrect code example:

    *** Settings ***
    Documentation    Only one empty line after this section.

    *** Keywords ***
    Keyword Definition
        No Operation

Correct code:

    *** Settings ***
    Documentation    Only one empty line after this section.


    *** Keywords ***
    Keyword Definition
        No Operation

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-sections](https://docs.robotframework.org/docs/style_guide#spacing-after-sections)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-sections.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-sections.severity=W"
        ]
        ```

??? example "empty_lines"

    Number of empty lines required between sections

    **Default value:** 2

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-sections.empty_lines=2
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-sections.empty_lines=2"
        ]
        ```

---

### SPC04: empty-lines-between-test-cases

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 1004

Fix availability: There is no automatic fix.

**Message**:

`Invalid number of empty lines between test cases ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Invalid number of empty lines between test cases.

Ensure there is the same number of empty lines between test cases for consistency and readability.

Incorrect code example:

    *** Test Cases ***
    First test case
        No Operation


    Second test case
        No Operation

Correct code:

    *** Test Cases ***
    First test case
        No Operation

    Second test case
        No Operation

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-test-cases-or-tasks](https://docs.robotframework.org/docs/style_guide#spacing-after-test-cases-or-tasks)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-test-cases.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-test-cases.severity=W"
        ]
        ```

??? example "empty_lines"

    Number of empty lines required between test cases

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-test-cases.empty_lines=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-test-cases.empty_lines=1"
        ]
        ```

---

### SPC05: empty-lines-between-keywords

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 1005

Fix availability: There is no automatic fix.

**Message**:

`Invalid number of empty lines between keywords ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Invalid number of empty lines between keywords.

Ensure there is the same number of empty lines between keywords for consistency and readability.

Incorrect code example:

    *** Keywords ***
    First Keyword
        No Operation


    Second Keyword
        No Operation

Correct code:

    *** Keywords ***
    First Keyword
        No Operation

    Second Keyword
        No Operation

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-keywords](https://docs.robotframework.org/docs/style_guide#spacing-after-keywords)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-keywords.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-keywords.severity=W"
        ]
        ```

??? example "empty_lines"

    Number of empty lines required between keywords

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-between-keywords.empty_lines=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-between-keywords.empty_lines=1"
        ]
        ```

---

### SPC06: mixed-tabs-and-spaces

Added: `v1.1.0`

Supported RF version `All`

Deprecated names: 1006

Fix availability: There is no automatic fix.

**Message**:

`Inconsistent use of tabs and spaces in file`

**Documentation**:

Mixed tabs and spaces in the file.

File contains both spaces and tabs. Use only one type of separators - preferably spaces.

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
(``robocop format``) to fix it.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure mixed-tabs-and-spaces.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "mixed-tabs-and-spaces.severity=W"
        ]
        ```

---

### SPC08: bad-indent

Added: `v3.0.0`

Supported RF version `All`

Deprecated names: 1008

Fix availability: There is no automatic fix.

**Message**:

`{bad_indent_msg}`

**Documentation**:

Line is misaligned or indent is invalid.

This rule reports a warning if the line is misaligned in the current block.
The correct indentation is determined by the most common indentation in the current block.
It is possible to switch for stricter mode using the `` indent `` parameter (default ``-1``).

Incorrect code example:

    *** Keywords ***
    Keyword
        Keyword Call
         Misaligned Keyword Call
        IF    $condition    RETURN
       Keyword Call

Correct code:

    *** Keywords ***
    Keyword
        Keyword Call
        Misaligned Keyword Call
        IF    $condition    RETURN
        Keyword Call

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#indentation](https://docs.robotframework.org/docs/style_guide#indentation)
- [#block-indentation](https://docs.robotframework.org/docs/style_guide#block-indentation)
- [#indentation-within-test-cases-tasks-and-keywords-section](https://docs.robotframework.org/docs/style_guide#indentation-within-test-cases-tasks-and-keywords-section)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure bad-indent.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "bad-indent.severity=W"
        ]
        ```

??? example "indent"

    Number of spaces per indentation level

    **Default value:** -1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure bad-indent.indent=-1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "bad-indent.indent=-1"
        ]
        ```

---

### SPC09: empty-line-after-section

Added: `v1.2.0`

Supported RF version `All`

Deprecated names: 1009

Fix availability: There is no automatic fix.

**Message**:

`Too many empty lines after '{section_name}' section header ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Too many empty lines after the section header.

Empty lines after the section header are not allowed by default.

Incorrect code example:

     *** Test Cases ***

     Test case name

Correct code:

     *** Test Cases ***
     Test case name

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-the-section-header-line](https://docs.robotframework.org/docs/style_guide#spacing-after-the-section-header-line)

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `empty_lines` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `empty_lines` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-line-after-section.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-line-after-section.severity=W"
        ]
        ```

??? example "empty_lines"

    Number of empty lines allowed after section header

    **Default value:** 0

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-line-after-section.empty_lines=0
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-line-after-section.empty_lines=0"
        ]
        ```

---

### SPC10: too-many-trailing-blank-lines

Added: `v1.4.0`

Supported RF version `All`

Deprecated names: 1010

Fix availability: There is no automatic fix.

**Message**:

`Too many blank lines at the end of file`

**Documentation**:

Too many blank lines at the end of the file.

There should be exactly one blank line at the end of the file.

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-after-sections](https://docs.robotframework.org/docs/style_guide#spacing-after-sections)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure too-many-trailing-blank-lines.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "too-many-trailing-blank-lines.severity=W"
        ]
        ```

---

### SPC11: misaligned-continuation

Added: `v1.6.0`

Supported RF version `All`

Deprecated names: 1011

Fix availability: There is no automatic fix.

**Message**:

`Continuation marker is not aligned with starting row`

**Documentation**:

Misaligned continuation marker.

Incorrect code example:

    *** Settings ***
        Default Tags       default tag 1    default tag 2    default tag 3
    ...                default tag 4    default tag 5

    *** Test Cases ***
    Example
        Do X    first argument    second argument    third argument
      ...    fourth argument    fifth argument    sixth argument

Correct code:

    *** Settings ***
    Default Tags       default tag 1    default tag 2    default tag 3
    ...                default tag 4    default tag 5

    *** Test Cases ***
    Example
        Do X    first argument    second argument    third argument
        ...    fourth argument    fifth argument    sixth argument

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#variables-section-line-continuation](https://docs.robotframework.org/docs/style_guide#variables-section-line-continuation)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure misaligned-continuation.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "misaligned-continuation.severity=W"
        ]
        ```

---

### SPC12: consecutive-empty-lines

Added: `v1.8.0`

Supported RF version `All`

Deprecated names: 1012

Fix availability: There is no automatic fix.

**Message**:

`Too many consecutive empty lines ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Too many consecutive empty lines.

Incorrect code example:

    *** Variables ***
    ${VAR}    value


    ${VAR2}    value


    *** Keywords ***
    Keyword
        Step 1


        Step 2

Correct code:

    *** Variables ***
    ${VAR}    value
    ${VAR2}    value


    *** Keywords ***
    Keyword
        Step 1
        Step 2  # 1 empty line is also fine, but no more

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#settings-1](https://docs.robotframework.org/docs/style_guide#settings-1)
- [#spacing-between-code-blocks-within-test-cases-or-tasks](https://docs.robotframework.org/docs/style_guide#spacing-between-code-blocks-within-test-cases-or-tasks)
- [#spacing-between-code-blocks-within-keyword-calls](https://docs.robotframework.org/docs/style_guide#spacing-between-code-blocks-within-keyword-calls)

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `empty_lines` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `empty_lines` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure consecutive-empty-lines.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "consecutive-empty-lines.severity=W"
        ]
        ```

??? example "empty_lines"

    Number of allowed consecutive empty lines

    **Default value:** 1

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure consecutive-empty-lines.empty_lines=1
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "consecutive-empty-lines.empty_lines=1"
        ]
        ```

---

### SPC13: empty-lines-in-statement

Added: `v1.8.0`

Supported RF version `All`

Deprecated names: 1013

Fix availability: There is no automatic fix.

**Message**:

`Multi-line statement with empty lines`

**Documentation**:

Multi-line statement with empty lines.

Avoid using empty lines between continuation markers in multi line statement.

Incorrect code example:

    *** Test Cases ***
    Test case
        Keyword
        ...  1
        # empty line in-between multiline statement
        ...  2

        ...  3

Correct code:

    *** Test Cases ***
    Test case
        Keyword
        ...  1
        ...  2
        ...  3

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#spacing-of-line-continuations](https://docs.robotframework.org/docs/style_guide#spacing-of-line-continuations)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-in-statement.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-in-statement.severity=W"
        ]
        ```

---

### SPC14: variable-not-left-aligned

Added: `v1.8.0`

Supported RF version `>=4.0`

Deprecated names: 1014, variable-should-be-left-aligned

Fix availability: There is no automatic fix.

**Message**:

`Variable in Variables section is not left aligned`

**Documentation**:

Variable in ``*** Variables ***`` section should be left aligned.

Incorrect code example:

    *** Variables ***
     ${VAR}  1
      ${VAR2}  2

Correct code:

    *** Variables ***
    ${VAR}  1
    ${VAR2}  2

This rule is not fixed by ``robocop check --fix``. Use the ``AlignVariablesSection`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#indentation-within-variables-section](https://docs.robotframework.org/docs/style_guide#indentation-within-variables-section)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure variable-not-left-aligned.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "variable-not-left-aligned.severity=E"
        ]
        ```

---

### SPC15: misaligned-continuation-row

Added: `v1.11.0`

Supported RF version `All`

Deprecated names: 1015

Fix availability: There is no automatic fix.

**Message**:

`Continuation line is not aligned with the previous one`

**Documentation**:

The continuation marker should be aligned with the previous one.

Incorrect code example:

    *** Variable ***
    ${VAR}    This is a long string.
    ...       It has multiple sentences.
    ...         And this line is misaligned with previous one.

    *** Test Cases ***
    My Test
        My Keyword
        ...    arg1
        ...   arg2  # misaligned

Correct code:

    *** Variable ***
    ${VAR}    This is a long string.
    ...       It has multiple sentences.
    ...       And this line is misaligned with previous one.

    *** Test Cases ***
    My Test
        My Keyword
        ...    arg1
        ...    arg2  # misaligned

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
(``robocop format``) to fix it.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure misaligned-continuation-row.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "misaligned-continuation-row.severity=W"
        ]
        ```

??? example "ignore_docs"

    Ignore documentation

    **Default value:** True

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure misaligned-continuation-row.ignore_docs=True
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "misaligned-continuation-row.ignore_docs=True"
        ]
        ```

??? example "ignore_run_keywords"

    Ignore run keywords

    **Default value:** False

    **Type:** bool

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure misaligned-continuation-row.ignore_run_keywords=False
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "misaligned-continuation-row.ignore_run_keywords=False"
        ]
        ```

---

### SPC16: suite-setting-not-left-aligned

Added: `v2.4.0`

Supported RF version `>=4.0`

Deprecated names: 1016, suite-setting-should-be-left-aligned

Fix availability: There is no automatic fix.

**Message**:

`Setting in Settings section is not left aligned`

**Documentation**:

Settings in the ``*** Settings ***`` section should be left aligned.

Incorrect code example:

    *** Settings ***
        Library  Collections
    Resource  data.resource
        Variables  vars.robot

Correct code:

    *** Settings ***
    Library  Collections
    Resource  data.resource
    Variables  vars.robot

**Style guide**:

- [#indentation-within-settings-section](https://docs.robotframework.org/docs/style_guide#indentation-within-settings-section)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure suite-setting-not-left-aligned.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "suite-setting-not-left-aligned.severity=E"
        ]
        ```

---

### SPC17: bad-block-indent

Added: `v3.0.0`

Supported RF version `All`

Deprecated names: 1017

Fix availability: There is no automatic fix.

**Message**:

`Not enough indentation inside block`

**Documentation**:

Not enough indentation.

Reports occurrences where indentation is less than two spaces than current block parent element (such as
``FOR``/``IF``/``WHILE``/``TRY`` header).

Incorrect code example:

    *** Keywords ***
    Some Keyword
        FOR  ${elem}  IN  ${list}
            Log  ${elem}  # this is fine
       Log  stuff    # this is bad indent
    # bad comment
        END

Correct code:

    *** Keywords ***
    Some Keyword
        FOR  ${elem}  IN  ${list}
            Log  ${elem}  # this is fine
            Log  stuff    # this is bad indent
            # bad comment
        END

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
(``robocop format``) to fix it.

**Style guide**:

- [#indentation](https://docs.robotframework.org/docs/style_guide#indentation)

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure bad-block-indent.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "bad-block-indent.severity=E"
        ]
        ```

---

### SPC18: first-argument-in-new-line

Added: `v5.3.0`

Supported RF version `All`

Deprecated names: 1018

Fix availability: There is no automatic fix.

**Message**:

`First argument: '{argument_name}' is not placed on the same line as [Arguments] setting`

**Documentation**:

The first argument is not in the same level as the ``[Arguments]`` setting.

Incorrect code example:

    *** Keywords ***
    Custom Keyword With Five Required Arguments
    [Arguments]
    ...    ${name}
    ...    ${surname}

Correct code:

    *** Keywords ***
    Custom Keyword With Five Required Arguments
    [Arguments]    ${name}
    ...    ${surname}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure first-argument-in-new-line.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "first-argument-in-new-line.severity=W"
        ]
        ```

---

### SPC19: not-enough-whitespace-after-setting

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0402

Fix availability: Fix is always available.

**Message**:

`Not enough whitespace after '{setting_name}' setting`

**Documentation**:

Not enough whitespace after setting.

Provide at least two spaces after setting.

Incorrect code example:

    *** Test Cases ***
    Test
        [Documentation] doc
        Keyword

    *** Keywords ***
    Keyword
        [Documentation]  This is doc
        [Arguments] ${var}
        Should Be True  ${var}

Correct code:

    *** Test Cases ***
    Test
        [Documentation]  doc
        Keyword

    *** Keywords ***
    Keyword
        [Documentation]  This is doc
        [Arguments]    ${var}
        Should Be True  ${var}

The separator can be expanded automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-enough-whitespace-after-setting.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-enough-whitespace-after-setting.severity=E"
        ]
        ```

---

### SPC20: not-enough-whitespace-after-newline-marker

Added: `v1.11.0`

Supported RF version `All`

Deprecated names: 0406

Fix availability: Fix is always available.

**Message**:

`Not enough whitespace after '...' marker`

**Documentation**:

Not enough whitespace after a newline marker.

Provide at least two spaces after a newline marker.

Incorrect code example:

    *** Variables ***
    @{LIST}  1
    ... 2
    ...  3

Correct code:

    *** Variables ***
    @{LIST}  1
    ...  2
    ...  3

The separator can be expanded automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-enough-whitespace-after-newline-marker.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-enough-whitespace-after-newline-marker.severity=E"
        ]
        ```

---

### SPC21: not-enough-whitespace-after-variable

Added: `v1.11.0`

Supported RF version `>=4.0`

Deprecated names: 0410

Fix availability: Fix is always available.

**Message**:

`Not enough whitespace after '{variable_name}' variable name`

**Documentation**:

Not enough whitespace after variable.

Provide at least two spaces after the variable name.

Incorrect code example:

    *** Variables ***
    ${variable} 1
    ${other_var}  2

Correct code:

    *** Variables ***
    ${variable}  1
    ${other_var}  2

The separator can be expanded automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-enough-whitespace-after-variable.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-enough-whitespace-after-variable.severity=E"
        ]
        ```

---

### SPC22: not-enough-whitespace-after-suite-setting

Added: `v1.11.0`

Supported RF version `All`

Deprecated names: 0411

Fix availability: Fix is always available.

**Message**:

`Not enough whitespace after '{setting_name}' setting`

**Documentation**:

Not enough whitespace after suite setting.

Provide at least two spaces after the suite setting.

Incorrect code example:

    *** Settings ***
    Library Collections
    Test Tags  tag
    ...  tag2
    Suite Setup Keyword

Correct code:

    *** Settings ***
    Library    Collections
    Test Tags  tag
    ...  tag2
    Suite Setup    Keyword

The separator can be expanded automatically with the ``--fix`` option.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure not-enough-whitespace-after-suite-setting.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "not-enough-whitespace-after-suite-setting.severity=E"
        ]
        ```

---

### SPC23: empty-line-in-test-template

Added: `v9.0.0`

Supported RF version `>=5.0`

Fix availability: Fix is always available.

**Message**:

`Empty line in test template data`

**Documentation**:

Empty line in test template data.

Robot Framework ignores empty lines between data rows in templated tests. Remove these lines so that the test data
does not contain rows that have no effect.

Incorrect code example:

    *** Test Cases ***
    Example
        [Template]    Template Keyword
        first argument

        second argument

Correct code:

    *** Test Cases ***
    Example
        [Template]    Template Keyword
        first argument
        second argument

The rule reports only empty lines between consecutive template data rows, including rows nested in control
structures. Blank lines next to settings or comments and blank lines separating test cases are preserved.

The fix removes the ignored empty line.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-line-in-test-template.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-line-in-test-template.severity=W"
        ]
        ```

---

### SPC24: empty-lines-inside-block

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Empty lines {block_position} ({empty_lines}/{allowed_empty_lines})`

**Documentation**:

Empty lines after a block header or before the block end.

Empty lines directly after a block header (``FOR``, ``WHILE``, ``IF``/``ELSE``, ``TRY``/``EXCEPT`` or ``GROUP``)
or directly before the block end are not allowed by default.

Incorrect code example:

    *** Keywords ***
    Iterate
        FOR    ${var}    IN    1    2

            Keyword Call

        END

Correct code:

    *** Keywords ***
    Iterate
        FOR    ${var}    IN    1    2
            Keyword Call
        END

The number of allowed empty lines can be configured using the ``empty_lines`` parameter::

    robocop check --configure empty-lines-inside-block.empty_lines=1

This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
(``robocop format``) to fix it.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `empty_lines` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `empty_lines` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-inside-block.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-inside-block.severity=I"
        ]
        ```

??? example "empty_lines"

    Number of allowed empty lines after a block header or before the block end

    **Default value:** 0

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-lines-inside-block.empty_lines=0
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-lines-inside-block.empty_lines=0"
        ]
        ```

## Tags

Rules for  tags.

### TAG01: tag-with-space

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0601

Fix availability: There is no automatic fix.

**Message**:

`Tag '{tag}' contains spaces`

**Documentation**:

Tag with space.

When including or excluding tags, it may lead to unexpected behavior. It's recommended to use short tag names
without spaces.

Example of rule violation:

    *** Test Cases ***
    Test
        [Tags]  tag with space    ${tag with space}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure tag-with-space.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "tag-with-space.severity=W"
        ]
        ```

---

### TAG02: tag-with-or-and

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0602

Fix availability: There is no automatic fix.

**Message**:

`Tag '{tag}' with reserved word OR/AND`

**Documentation**:

``OR`` or ``AND`` keyword found in the tag.

``OR`` and ``AND`` words are used to combine tags when selecting tests to be run in Robot Framework. Using
the following configuration:

    robocop check --include tagANDtag2

Robot Framework will only execute tests that contain ``tag`` and ``tag2``. That's why it's best to avoid ``AND``
and ``OR`` in tag names. See [docs](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#tag-patterns)
for more information.

Tag matching is case-insensitive. If your tag contains ``OR`` or ``AND`` you can use lowercase to match it.
For example, if your tag is ``PORT``, you can match it with ``port``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure tag-with-or-and.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "tag-with-or-and.severity=I"
        ]
        ```

---

### TAG03: tag-with-reserved-word

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0603

Fix availability: There is no automatic fix.

**Message**:

`Tag '{tag}' prefixed with reserved word `robot:``

**Documentation**:

Tag is prefixed with reserved work ``robot:``.

``robot:`` prefix is used by Robot Framework special tags. More details in
[RF User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#reserved-tags).
Special tags that are currently in use:

    - robot:exit
    - robot:flatten
    - robot:no-dry-run
    - robot:continue-on-failure
    - robot:recursive-continue-on-failure
    - robot:skip
    - robot:skip-on-failure
    - robot:stop-on-failure
    - robot:recursive-stop-on-failure
    - robot:exclude
    - robot:private

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure tag-with-reserved-word.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "tag-with-reserved-word.severity=W"
        ]
        ```

---

### TAG05: could-be-test-tags

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0605

Fix availability: There is no automatic fix.

**Message**:

`All tests in suite share these tags: '{tags}'`

**Documentation**:

All tests share the same tags which can be moved to the ``Test Tags`` setting.

Example:

    *** Test Cases ***
    Test
        [Tags]  featureX  smoke
        Step

    Test 2
        [Tags]  featureX
        Step

In this example all tests share one common tag ``featureX``. It can be declared just once using ``Test Tags``
or ``Task Tags``.
This rule was renamed from ``could-be-force-tags`` to ``could-be-test-tags`` in Robocop 2.6.0.

Will ignore `robot:*` tags.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure could-be-test-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "could-be-test-tags.severity=W"
        ]
        ```

---

### TAG06: tag-already-set-in-test-tags

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0606

Fix availability: Fix is always available.

**Message**:

`Tag '{tag}' is already set by {test_force_tags} in suite settings`

**Documentation**:

Tag is already set in the ``Test Tags`` setting.

Avoid repeating the same tags in tests when the tag is already declared in ``Test Tags`` or ``Force Tags``.
Example of rule violation:

    *** Settings ***
    Test Tags  common_tag

    *** Test Cases ***
    Test
        [Tags]  sanity  common_tag
        Some Keyword

This rule was renamed from ``tag-already-set-in-force-tags`` to ``tag-already-set-in-test-tags`` in
Robocop 2.6.0.

The fix removes the redundant tag. If it is the only tag in the ``[Tags]`` setting, the whole setting is
removed - unless the suite defines ``Default Tags``, in which case the explicit ``NONE`` value is used
instead. Comments are never removed by the fix.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure tag-already-set-in-test-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "tag-already-set-in-test-tags.severity=W"
        ]
        ```

---

### TAG07: unnecessary-default-tags

Added: `v1.0.0`

Supported RF version `All`

Deprecated names: 0607

Fix availability: Fix is always available.

**Message**:

`Tags defined in Default Tags are always overwritten`

**Documentation**:

``Default Tags`` setting is always overwritten and is unnecessary.

Example of rule violation:

    *** Settings ***
    Default Tags  tag1  tag2

    *** Test Cases ***
    Test
        [Tags]  tag3
        Step

    Test 2
        [Tags]  tag4
        Step

Since ``Test`` and ``Test 2`` have the ``[Tags]`` section, the ``Default Tags`` setting is never used.

The fix removes the ``Default Tags`` setting. Comments are not removed.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unnecessary-default-tags.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unnecessary-default-tags.severity=I"
        ]
        ```

---

### TAG08: empty-tags

Added: `v2.0.0`

Supported RF version `All`

Deprecated names: 0608

Fix availability: Fix is always available.

**Message**:

`[Tags] setting without values{optional_warning}`

**Documentation**:

``[Tags]`` setting without any value.

If you want to use empty ``[Tags]`` (for example, to overwrite ``Default Tags``), then use the ``NONE`` value
to be explicit.

Incorrect code example:

    *** Settings ***
    Default Tags    tag


    *** Test Cases ***
    Test without tags
        [Tags]
        Keyword Call

Correct code example:

    *** Settings ***
    Default Tags    tag


    *** Test Cases ***
    Test without tags
        [Tags]    NONE
        Keyword Call

The fix removes the empty ``[Tags]`` setting. If the suite defines ``Default Tags``, the test case ``[Tags]``
is not removed but filled with the explicit ``NONE`` value instead, since the empty ``[Tags]`` overwrites the
``Default Tags``. Comments are never removed by the fix.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-tags.severity=W"
        ]
        ```

---

### TAG09: duplicated-tags

Added: `v2.0.0`

Supported RF version `All`

Deprecated names: 0609

Fix availability: Fix is sometimes available.

**Message**:

`Multiple tags with name '{name}' (first occurrence at line {line} column {column})`

**Documentation**:

Duplicated tags found.

Tags are free text, but they are normalized so that they are converted to lowercase and all spaces are removed.
Only the first tag is used, other occurrences are ignored.

Example of duplicated tags:

    *** Test Cases ***
    Test
        [Tags]    Tag    TAG    tag    t a g

The fix removes the duplicated tags and leaves only the first occurrence. Tags defined in the keyword
documentation are not fixed. Comments are never removed by the fix.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-tags.severity=W"
        ]
        ```

---

### TAG10: could-be-keyword-tags

Added: `v3.3.0`

Supported RF version `>=6`

Deprecated names: 0610

Fix availability: There is no automatic fix.

**Message**:

`All keywords in suite share these tags: '{tags}'`

**Documentation**:

All keywords share the same tags which can be moved to the ``Keyword Tags`` setting.

Example:

    *** Keywords ***
    Keyword
        [Tags]  featureX  smoke
        Step

    Keyword
        [Tags]  featureX
        Step

In this example all keywords share one common tag ``featureX``.It can be declared just once using
``Keyword Tags``.

Will ignore `robot:*` tags.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure could-be-keyword-tags.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "could-be-keyword-tags.severity=I"
        ]
        ```

---

### TAG11: tag-already-set-in-keyword-tags

Added: `v3.3.0`

Supported RF version `>=6`

Deprecated names: 0611

Fix availability: Fix is always available.

**Message**:

`Tag '{tag}' is already set by {keyword_tags} in suite settings`

**Documentation**:

Tag is already set in the ``Test Keyword`` setting.

Avoid repeating the same tags in keywords when the tag is already declared in ``Keyword Tags``.
Example of rule violation:

    *** Settings ***
    Keyword Tags  common_tag

    *** Keywords ***
    Keyword
        [Tags]  sanity  common_tag

The fix removes the redundant tag. If it is the only tag in the ``[Tags]`` setting, the whole setting is
removed. Comments are never removed by the fix.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure tag-already-set-in-keyword-tags.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "tag-already-set-in-keyword-tags.severity=W"
        ]
        ```

---

### TAG12: unnecessary-continue-on-failure

Added: `v8.9.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`'{keyword_name}' is not needed when the '{tag}' tag is used`

**Documentation**:

``Run Keyword And Continue On Failure`` is not needed when the continue on failure tag is set.

``robot:continue-on-failure`` and ``robot:recursive-continue-on-failure`` tags already make all the keywords
in the test or keyword body run even if one of them fails. Wrapping such calls in
``Run Keyword And Continue On Failure`` only adds noise.

Example of rule violation:

    *** Test Cases ***
    Test
        [Tags]    robot:continue-on-failure
        Run Keyword And Continue On Failure    Should Be Equal    ${expected}    ${actual}

It can be rewritten to:

    *** Test Cases ***
    Test
        [Tags]    robot:continue-on-failure
        Should Be Equal    ${expected}    ${actual}

Keyword calls nested inside ``FOR``, ``WHILE``, ``IF`` or ``TRY`` blocks are reported as well, since the tag
also makes them continue on failure. Calls that assign a return value are ignored.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unnecessary-continue-on-failure.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unnecessary-continue-on-failure.severity=I"
        ]
        ```

---

### TAG13: could-be-continue-on-failure-tag

Added: `v8.9.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`{block_name} '{name}' uses 'Run Keyword And Continue On Failure' {call_count} times and could use the 'robot:continue-on-failure' tag instead`

**Documentation**:

Every keyword call is wrapped in ``Run Keyword And Continue On Failure``.

If all the keyword calls in the test or keyword body are wrapped in ``Run Keyword And Continue On Failure``,
the ``robot:continue-on-failure`` tag can be used instead. It makes the data shorter and easier to read.

Example of rule violation:

    *** Keywords ***
    Validate Stuff
        Run Keyword And Continue On Failure    Should Be Equal    ${expected_id}    ${actual_id}
        Run Keyword And Continue On Failure    Should Be Equal    ${expected_name}    ${actual_name}

It can be rewritten to:

    *** Keywords ***
    Validate Stuff
        [Tags]    robot:continue-on-failure
        Should Be Equal    ${expected_id}    ${actual_id}
        Should Be Equal    ${expected_name}    ${actual_name}

Note that ``robot:continue-on-failure`` is not applied to the keywords called from the body.
Use ``robot:recursive-continue-on-failure`` if the continue on failure mode should be inherited.

Configure ``min_calls`` to set how many wrapped calls are required to report the rule:

    robocop check --configure could-be-continue-on-failure-tag.min_calls=3

The rule is only reported if every keyword call in the body is wrapped. Calls nested inside ``FOR``, ``WHILE``,
``IF`` or ``TRY`` blocks are taken into account, since the tag affects them as well. Calls that assign a return
value are not equivalent to the tag and prevent the rule from being reported.

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `min_calls` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `min_calls` - its value should be lower or
> equal to the lowest value in the threshold.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure could-be-continue-on-failure-tag.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "could-be-continue-on-failure-tag.severity=I"
        ]
        ```

??? example "min_calls"

    Number of 'run keyword and continue on failure' calls required to report the rule

    **Default value:** 2

    **Type:** int

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure could-be-continue-on-failure-tag.min_calls=2
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "could-be-continue-on-failure-tag.min_calls=2"
        ]
        ```

## Variables

Rules for variables.

### VAR01: empty-variable

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0912

Fix availability: Fix is always available.

**Message**:

`Empty variable value`

**Documentation**:

Variable without value.

Variables with placeholder ${EMPTY} values are more explicit.

Incorrect code example:

    *** Variables ***
    ${VAR_NO_VALUE}
    ${VAR_WITH_EMPTY}    ${EMPTY}
    @{MULTILINE_FIRST_EMPTY}
    ...
    ...    value
    ${EMPTY_WITH_BACKSLASH}  \

Correct code:

    *** Keywords ***
    Create Variables
        VAR    @{var_no_value}
        VAR    ${var_with_empty}    ${EMPTY}

    Incorrect code example:

    *** Variables ***
    ${VAR_NO_VALUE}    ${EMPTY}
    ${VAR_WITH_EMPTY}    ${EMPTY}
    @{MULTILINE_FIRST_EMPTY}
    ...    ${EMPTY}
    ...    value
    ${EMPTY_WITH_BACKSLASH}  \


    *** Keywords ***
    Create Variables
        VAR    @{var_no_value}    @{EMPTY}
        VAR    ${var_with_empty}    ${EMPTY}

You can configure ``empty-variable`` rule to run only in ```*** Variables ***``` section or on
``VAR`` statements using ``variable_source`` parameter.

The fix adds the explicit empty value, using the variable type to select it: ``${EMPTY}`` for scalars,
``@{EMPTY}`` for lists and ``&{EMPTY}`` for dictionaries. Empty values in a list and the ``\`` values are
always replaced with ``${EMPTY}``.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-variable.severity=W"
        ]
        ```

??? example "variable_source"

    Variable sources that will be checked

    **Default value:** section,var

    **Type:** comma separated list

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure empty-variable.variable_source=section,var
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "empty-variable.variable_source=section,var"
        ]
        ```

---

### VAR02: unused-variable

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0920

Fix availability: There is no automatic fix.

**Message**:

`Variable '{name}' is assigned but not used`

**Documentation**:

Unused variable.

Incorrect code example:

    *** Keywords ***
    Get Triangle Base Points
        [Arguments]       ${triangle}
        ${p1}    ${p2}    ${p3}    Get Triangle Points    ${triangle}
        Log      Triangle base points are: ${p1} and ${p2}.
        RETURN   ${p1}    ${p2}  # ${p3} is never used

You can use ``${_}`` variable name or start variable name with ``_`` underscore if you purposefully do not
use variable:

    *** Keywords ***
    Process Value 10 Times
        [Arguments]    ${value}
        FOR    ${_}   IN RANGE    10
            Process Value    ${value}
        END
        ${_first}    ${second}    Unpack List    @{LIST}

Note that some keywords may use your local variables even if you don't pass them directly. For example,
BuiltIn ``Replace Variables`` or any custom keyword that retrieves variables from a local scope. In this case,
Robocop will still raise an ``unused-variable`` even if the variable is actually used.

You can configure the rule to ignore specific variable names in the ``*** Variables ***`` section using
the ``ignore`` parameter. This is useful for variables that are used by external listeners, libraries,
or variable files:

    robocop check --configure unused-variable.ignore=suite_param,other_var

Variable names are matched case-insensitively following Robot Framework conventions.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-variable.severity=W"
        ]
        ```

??? example "ignore"

    Comma-separated list of variable names to ignore in *** variables *** section (case-insensitive)

    **Default value:** 

    **Type:** comma separated list

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure unused-variable.ignore=
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "unused-variable.ignore="
        ]
        ```

---

### VAR03: variable-overwritten-before-usage

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0922

Fix availability: There is no automatic fix.

**Message**:

`Local variable '{name}' is overwritten before usage`

**Documentation**:

Local variable is overwritten before usage.

Local variable in Keyword, Test Case or Task is overwritten before it is used:

    *** Keywords ***
    Overwritten Variable
        ${value}    Keyword
        ${value}    Keyword

In case the value of the variable is not important, it is possible to use ``${_}`` name:

    *** Test Cases ***
    Call keyword and ignore some return values
        ${_}    ${item}    Unpack List    @{LIST}
        FOR    ${_}    IN RANGE  10
            Log    Run this code 10 times.
        END

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure variable-overwritten-before-usage.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "variable-overwritten-before-usage.severity=W"
        ]
        ```

---

### VAR04: no-global-variable

Added: `v5.6.0`

Supported RF version `All`

Deprecated names: 0929

Fix availability: There is no automatic fix.

**Message**:

`Variable with global scope defined outside variables section`

**Documentation**:

Global variable defined outside the ``*** Variables ***`` section.

Setting or updating global variables in a test/keyword often leads to hard-to-understand
code. In most cases, you're better off using local variables.

Changes in global variables during a test are hard to track because you must remember what's
happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
up your understanding of what the code should be doing.

Local variables don't suffer from this issue because they are always created in the
keyword/test you're looking at.

In this example, the keyword changes the global variable. This will cause the test to fail.
Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
remember the seemingly unrelated keyword:

    *** Variables ***
    ${hello}    Hello, world!

    *** Test Cases ***
    My Amazing Test
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        Set Global Variable    ${hello}    Goodnight, moon!

Using the VAR-syntax:

    *** Variables ***
    ${hello}    Hello, world!

    *** Test Cases ***
    My Amazing Test
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        VAR    ${hello}    Goodnight, moon!    scope=GLOBAL

In some specific situations, global variables are a great tool. But most of the time, it
makes code needlessly hard to understand.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure no-global-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "no-global-variable.severity=W"
        ]
        ```

---

### VAR05: no-suite-variable

Added: `v5.6.0`

Supported RF version `All`

Deprecated names: 0930

Fix availability: There is no automatic fix.

**Message**:

`Variable defined with suite scope`

**Documentation**:

Using suite variables in a test/keyword often leads to hard-to-understand code. In most
cases, you're better off using local variables.

Changes in suite variables during a test are hard to track because you must remember what's
happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
up your understanding of what the code should be doing.

Local variables don't suffer from this issue because they are always created in the
keyword/test you're looking at.

In this example, the keyword changes the suite variable. This will cause the test to fail.
Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
remember the seemingly unrelated keyword:

    *** Test Cases ***
    My Amazing Test
        Set Suite Variable    ${hello}    Hello, world!
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        Set Suite Variable    ${hello}    Goodnight, moon!

Using the VAR-syntax:

    *** Test Cases ***
    My Amazing Test
        VAR    ${hello}    Hello, world!    scope=SUITE
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        VAR    ${hello}    Goodnight, moon!    scope=SUITE

In some specific situations, suite variables are a great tool. But most of the time, it
makes code needlessly hard to understand.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure no-suite-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "no-suite-variable.severity=W"
        ]
        ```

---

### VAR06: no-test-variable

Added: `v5.6.0`

Supported RF version `All`

Deprecated names: 0931

Fix availability: There is no automatic fix.

**Message**:

`Variable defined with test/task scope`

**Documentation**:

Using test/task variables in a test/keyword often leads to hard-to-understand code. In most
cases, you're better off using local variables.

Changes in test/task variables during a test are hard to track because you must remember what's
happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
up your understanding of what the code should be doing.

Local variables don't suffer from this issue because they are always created in the
keyword/test you're looking at.

In this example, the keyword changes the test/task variable. This will cause the test to fail.
Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
remember the seemingly unrelated keyword:

    *** Test Cases ***
    My Amazing Test
        Set Test Variable    ${hello}    Hello, world!
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        Set Test Variable    ${hello}    Goodnight, moon!

Using the VAR-syntax:

    *** Test Cases ***
    My Amazing Test
        VAR    ${hello}    Hello, world!    scope=TEST
        Do A Thing
        Should Be Equal    ${hello}    Hello, world!

    *** Keywords ***
    Do A Thing
        VAR    ${hello}    Goodnight, moon!    scope=TEST

In some specific situations, test/task variables are a great tool. But most of the time, it
makes code needlessly hard to understand.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure no-test-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "no-test-variable.severity=W"
        ]
        ```

---

### VAR07: non-local-variables-should-be-uppercase

Added: `v1.4.0`

Supported RF version `All`

Deprecated names: 0310

Fix availability: There is no automatic fix.

**Message**:

`Non local variable is not uppercase`

**Documentation**:

Non-local variable is not uppercase.

Non-local variable is not uppercase to easily identify scope of the variable.

Incorrect code example:

    *** Test Cases ***
    Test case
        Set Task Variable    ${my_var}           1
        Set Suite Variable   ${My Var}           1
        Set Test Variable    ${myvar}            1
        Set Global Variable  ${my_var${NESTED}}  1

Correct code:

    *** Test Cases ***
    Test case
        Set Task Variable    ${MY_VAR}           1
        Set Suite Variable   ${MY VAR}           1
        Set Test Variable    ${MY_VAR}           1
        Set Global Variable  ${MY VAR${nested}}  1

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure non-local-variables-should-be-uppercase.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "non-local-variables-should-be-uppercase.severity=W"
        ]
        ```

---

### VAR08: possible-variable-overwriting

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0316

Fix availability: There is no automatic fix.

**Message**:

`Variable '{variable_name}' may overwrite similar variable inside '{block_name}' {block_type}`

**Documentation**:

Variable may overwrite similar variable inside code block.

Variable names are case-insensitive, and also spaces and underscores are ignored.
Following assignments overwrite the same variable:

    *** Keywords ***
    Retrieve Usernames
        ${username}      Get Username       id=1
        ${User Name}     Get Username       id=2
        ${user_name}     Get Username       id=3

Use consistent variable naming guidelines to avoid unintended variable overwriting.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure possible-variable-overwriting.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "possible-variable-overwriting.severity=W"
        ]
        ```

---

### VAR09: hyphen-in-variable-name

Added: `v1.10.0`

Supported RF version `All`

Deprecated names: 0317

Fix availability: There is no automatic fix.

**Message**:

`Hyphen in variable name '{variable_name}'`

**Documentation**:

Hyphen in the variable name.

Hyphens can be treated as minus sign by Robot Framework. If it is not intended, avoid using hyphen (``-``)
character in variable name.

Incorrect code example:

    *** Test Cases ***
    Test case
        ${var2}  Set Variable  ${${var}-${var2}}

That's why there is a possibility that hyphen in name is not recognized as part of the name but as a minus sign.
Better to use underscore instead:

Correct code:

    *** Test Cases ***
    Test case
        ${var2}  Set Variable  ${${var}_${var2}}

Hyphens in ``*** Variables ***`` section or in ``[Arguments]`` are also reported for consistency reason.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure hyphen-in-variable-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "hyphen-in-variable-name.severity=W"
        ]
        ```

---

### VAR10: inconsistent-variable-name

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0323

Fix availability: There is no automatic fix.

**Message**:

`Variable '{name}' has inconsistent naming. First used as '{first_use}'`

**Documentation**:

Variable with inconsistent naming.

Variable names are case-insensitive and ignore underscores and spaces. It is possible to
write the variable in multiple ways, and it will be a valid Robot Framework code. However,
it makes it harder to maintain the code that does not follow the consistent naming.

Incorrect code example:

    *** Keywords ***
    Check If User Is Admin
        [Arguments]    ${username}
        ${role}    Get User Role     ${username}
        IF    '${ROLE}' == 'Admin'   # inconsistent name with ${role}
            Log    ${Username} is an admin  # inconsistent name with ${username}
        ELSE
            Log    ${user name} is not an admin  # inconsistent name
        END

Correct code:

    *** Keywords ***
    Check If User Is Admin
        [Arguments]    ${username}
        ${role}    Get User Role     ${username}
        IF    '${role}' == 'Admin'
            Log    ${username} is an admin
        ELSE
            Log    ${username} is not an admin
        END

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure inconsistent-variable-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-variable-name.severity=W"
        ]
        ```

---

### VAR11: overwriting-reserved-variable

Added: `v3.2.0`

Supported RF version `All`

Deprecated names: 0324

Fix availability: There is no automatic fix.

**Message**:

`{var_or_arg} '{variable_name}' overwrites reserved variable '{reserved_variable}'`

**Documentation**:

Variable overwrites reserved variable.

Overwriting reserved variables may bring unexpected results.
For example, overwriting a variable with the name ``${LOG_LEVEL}`` can break Robot Framework logging.
See the full list of reserved variables at
[Robot Framework User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables).

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure overwriting-reserved-variable.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "overwriting-reserved-variable.severity=W"
        ]
        ```

---

### VAR12: duplicated-assigned-var-name

Added: `v1.12.0`

Supported RF version `All`

Deprecated names: 0812

Fix availability: There is no automatic fix.

**Message**:

`Assigned variable name '{variable_name}' is already used`

**Documentation**:

Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following variables
are duplicates:

    *** Test Cases ***
    Test
        ${var}  ${VAR}  ${v_ar}  ${v ar}  Keyword

It is possible to use `${_}` to note that variable name is not important and will not be used:

    *** Keywords ***
    Get Middle Element
        [Arguments]    ${list}
        ${_}    ${middle}    ${_}    Split List    ${list}
        RETURN    ${middle}

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure duplicated-assigned-var-name.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "duplicated-assigned-var-name.severity=W"
        ]
        ```

---

### VAR13: automatic-variable-not-available

Added: `v9.0.0`

Supported RF version `All`

Fix availability: There is no automatic fix.

**Message**:

`Automatic variable '{variable}' is not available in {context}; it is only available in {available_in}`

**Documentation**:

Automatic variable used in a context where Robot Framework does not provide it.

Robot Framework has several automatic variables whose availability is limited to a specific execution context:

- ``${TEST NAME}``, ``@{TEST TAGS}``, and ``${TEST DOCUMENTATION}`` are available while a test is running.
- ``${TEST STATUS}`` and ``${TEST MESSAGE}`` are available only in a test teardown.
- ``${SUITE STATUS}`` and ``${SUITE MESSAGE}`` are available only in a suite teardown.
- ``${KEYWORD STATUS}`` and ``${KEYWORD MESSAGE}`` are available only in a user keyword teardown.

Using one of these variables directly in another context fails at runtime:

    *** Test Cases ***
    Invalid automatic variables
        Log    ${KEYWORD STATUS}
        Log    ${TEST STATUS}
        [Teardown]    Log    ${SUITE STATUS}

Use each variable in the context where Robot Framework makes it available:

    *** Settings ***
    Suite Teardown    Log    ${SUITE STATUS}
    Test Teardown     Log    ${TEST STATUS}

    *** Test Cases ***
    Valid automatic variables
        Log    ${TEST NAME}

    *** Keywords ***
    Keyword with teardown
        No Operation
        [Teardown]    Log    ${KEYWORD STATUS}

Robocop deliberately does not report these variables inside user keyword definitions. A user keyword can be called
from a test, test teardown, suite teardown, or another user keyword teardown, so its actual execution context cannot
be determined reliably from the file where it is defined. For example, ``${TEST NAME}`` in a user keyword can be
valid when called by a test but invalid when called by a suite setup. This conservative behavior avoids presenting
call-context guesses as certain errors.

See the official
[automatic variable scope table](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables).
The rule has no automatic fix because choosing a replacement or moving code requires understanding its intent.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** W

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure automatic-variable-not-available.severity=W
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "automatic-variable-not-available.severity=W"
        ]
        ```

## Annotations

Rules for typing and annotations.

### ANN01: missing-section-variable-type

> Rule is disabled by default. Enable it by using ``--select missing-section-variable-type`` option.

Added: `v7.1.0`

Supported RF version `>=7.3`

Fix availability: There is no automatic fix.

**Message**:

`Variable '{variable_name}' is missing type annotation`

**Documentation**:

Section variable without type annotation.

Robot Framework 7.3 introduced type conversion for variables. This rule
enforces that variables in the ``*** Variables ***`` section have explicit
type annotations for better code clarity and automatic type conversion.

This rule also checks ``VAR`` statements and assignment expressions
(``${var} = Keyword``).

Incorrect code example (when rule is enabled):

    *** Variables ***
    ${NUMBER}    42

    *** Keywords ***
    Example
        VAR    ${local}    value
        ${result} =    Some Keyword

Correct code:

    *** Variables ***
    ${NUMBER: int}    42

    *** Keywords ***
    Example
        VAR    ${local: str}    value
        ${result: list} =    Some Keyword

This rule is disabled by default.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-section-variable-type.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-section-variable-type.severity=I"
        ]
        ```

---

### ANN02: missing-argument-type

> Rule is disabled by default. Enable it by using ``--select missing-argument-type`` option.

Added: `v7.1.0`

Supported RF version `>=7.3`

Fix availability: There is no automatic fix.

**Message**:

`Argument '{variable_name}' is missing type annotation`

**Documentation**:

Keyword argument without type annotation.

Robot Framework 7.3 introduced type conversion for variables. This rule
enforces that keyword arguments have explicit type annotations for better
code clarity and automatic type conversion.

Incorrect code example (when rule is enabled):

    *** Keywords ***
    Example
        [Arguments]    ${arg}    @{varargs}    &{kwargs}
        Log    ${arg}

Correct code:

    *** Keywords ***
    Example
        [Arguments]    ${arg: str}    @{varargs: list}    &{kwargs: dict}
        Log    ${arg}

This rule is disabled by default.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-argument-type.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-argument-type.severity=I"
        ]
        ```

---

### ANN03: missing-for-loop-variable-type

> Rule is disabled by default. Enable it by using ``--select missing-for-loop-variable-type`` option.

Added: `v7.1.0`

Supported RF version `>=7.3`

Fix availability: There is no automatic fix.

**Message**:

`FOR loop variable '{variable_name}' is missing type annotation`

**Documentation**:

FOR loop variable without type annotation.

Robot Framework 7.3 introduced type conversion for variables. This rule
enforces that FOR loop variables have explicit type annotations for better
code clarity and automatic type conversion.

Incorrect code example (when rule is enabled):

    *** Test Cases ***
    Example
        FOR    ${index}    IN RANGE    10
            Log    ${index}
        END

Correct code:

    *** Test Cases ***
    Example
        FOR    ${index: int}    IN RANGE    10
            Log    ${index}
        END

This rule is disabled by default.

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** I

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure missing-for-loop-variable-type.severity=I
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "missing-for-loop-variable-type.severity=I"
        ]
        ```

---

### ANN04: set-keyword-with-type

Added: `v8.0.0`

Supported RF version `>=7.3`

Fix availability: There is no automatic fix.

**Message**:

`Set variable keyword with variable type`

**Documentation**:

Set Test/Suite/Global Variable keyword with variable type.

Variable type conversion does not work with Set Test/Suite/Global Variable keywords:

    *** Keywords ***
    Set Variables
        Set Local Variable    ${variable: int}    1
        Set Suite Variable    ${variable: str}    value
        Set Test Variable    ${variable: list[str]}    value    value
        Set Task Variable    ${variable: int}    2
        Set Global Variable    ${variable: int}    3

The VAR syntax needs to be used instead:

    *** Keywords ***
    Set Variables
        VAR    ${variable: int}    1
        VAR    ${variable: str}    value
        VAR    ${variable: list[str]}    value    value
        VAR    ${variable: int}    2
        VAR    ${variable: int}    3

**Parameters**:

??? example "severity"

    Rule severity (e = error, w = warning, i = info)

    **Default value:** E

    **Type:** severity

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure set-keyword-with-type.severity=E
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "set-keyword-with-type.severity=E"
        ]
        ```
