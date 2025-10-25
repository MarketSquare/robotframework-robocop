# NormalizeAssignments

Normalize assignments.

It can change all assignment signs to either the most commonly used in a given file or a configured one.
Default behaviour is autodetect for assignments from Keyword Calls and removing assignment signs in
``*** Variables ***`` section. It can be freely configured.

{{ configure_hint("NormalizeAssignments") }}

In this code the most common is no equal sign at all. It should remove ``=`` signs from all lines:

=== "Before"

    ```robotframework
    *** Variables ***
    ${var} =  ${1}
    @{list}  a
    ...  b
    ...  c

    ${variable}=  10


    *** Keywords ***
    Keyword
        ${var}  Keyword1
        ${var}   Keyword2
        ${var}=    Keyword
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${var}  ${1}
    @{list}  a
    ...  b
    ...  c

    ${variable}  10


    *** Keywords ***
    Keyword
        ${var}  Keyword1
        ${var}   Keyword2
        ${var}    Keyword
    ```

You can configure that behaviour to automatically add desired equal sign with ``equal_sign_type``
(default ``autodetect``) and ``equal_sign_type_variables`` (default ``remove``) parameters.

Possible types are:

- ``autodetect``
- ``equal_sign`` ('=')
- ``space_and_equal_sign`` (' =')

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c NormalizeAssignments.equal_sign_type=space_and_equal_sign -c NormalizeAssignments.equal_sign_type_variables=autodetect
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeAssignments.equal_sign_type=space_and_equal_sign",
        "NormalizeAssignments.equal_sign_type_variables=autodetect"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Variables ***
    ${var}=  ${1}
    @{list}  a
    ...  b
    ...  c

    ${variable}=  10


    *** Keywords ***
    Keyword
        ${var}  Keyword1
        ${var}   Keyword2
        ${var}=    Keyword
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${var}=  ${1}
    @{list}=  a
    ...  b
    ...  c

    ${variable}=  10


    *** Keywords ***
    Keyword
        ${var} =  Keyword1
        ${var} =   Keyword2
        ${var} =    Keyword
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip all instances of a given type
of the code.
