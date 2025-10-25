# NormalizeTags

Normalize tag names by normalizing case and removing duplicates.

{{ configure_hint("NormalizeTags") }}

Supported cases:

- lowercase (default),
- uppercase
- titlecase

You can configure a case using ``case`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select NormalizeTags --configure NormalizeTags.case=uppercase
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "NormalizeTags"
    ]
    configure = [
        "NormalizeTags.case=uppercase"
    ]
    ```

You can remove duplicates without normalizing a case by setting ``normalize_case`` parameter to False:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select NormalizeTags --configure NormalizeTags.normalize_case=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "NormalizeTags"
    ]
    configure = [
        "NormalizeTags.normalize_case=False"
    ]
    ```

## Preserve formatting

Tags formatting like new lines, separators or comments position will be lost when using ``NormalizeTags``
formatter. You can preserve formatting by using ``preserve_format`` flag:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select NormalizeTags --configure NormalizeTags.preserve_format=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "NormalizeTags"
    ]
    configure = [
        "NormalizeTags.preserve_format=True"
    ]
    ```

The downside is that the duplications will not be removed when ``preserve_format`` is enabled.

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    NeedNormalization_Now    # Tell some
        ...    also_need_Normalization     # interesting story
        ...     TAG                        # about those tags
    ```

=== "After (default)"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    neednormalization_now    also_need_normalization    tag    # Tell some    # interesting story    # about those tags
    ```

=== "After (preserve_format=True)"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    neednormalization_now    # Tell some
        ...    also_need_normalization     # interesting story
        ...     tag                        # about those tags
    ```
