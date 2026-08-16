*** Test Cases ***
Standalone Comment Disabler
    # robocop: off=unused-variable
    Log    message

Inline Disabler
    No Operation  # robocop: off=NAME01

Noqa Disabler
    No Operation  # noqa

Multiple Rules In Directive
    No Operation  # robocop: off=NAME01,some-rule

Two Comments In Line
    No Operation  # robocop: off=NAME01  # noqa

Not Fixed - Text In The Comment
    No Operation  # robocop: off=NAME01  some-text robocop: off=some-rule

Not Fixed - Text After Directive
    No Operation  # robocop: off=NAME01 and some text


*** Keywords ***
Block Disabler
    # robocop: off=unused-variable
    Log    message
    # robocop: on=unused-variable
