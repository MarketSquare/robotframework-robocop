# NormalizeComments

Normalize comments.

{{ configure_hint("NormalizeComments") }}

Normalizes spacing after the beginning of the comment. Fixes ``missing-space-after-comment`` rule violations
from the Robocop.

=== "Before"

    ```robotframework
    *** Settings ***
    #linecomment
    ### header


    *** Keywords ***
    Keyword
        Step  #comment
    ```

=== "After"

    ```robotframework
    *** Settings ***
    # linecomment
    ### header


    *** Keywords ***
    Keyword
        Step  # comment
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip option](../skip_formatting.md#skip-option) (``--skip comments``)
