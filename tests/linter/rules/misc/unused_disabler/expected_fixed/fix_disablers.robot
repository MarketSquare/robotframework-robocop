*** Test Cases ***
Standalone Comment Disabler
    Log    message

Inline Disabler
    No Operation

Noqa Disabler
    No Operation

Multiple Rules In Directive
    No Operation

Two Comments In Line
    No Operation

Not Fixed - Text In The Comment
    No Operation  # robocop: off=NAME01  some-text robocop: off=some-rule

Not Fixed - Text After Directive
    No Operation  # robocop: off=NAME01 and some text


*** Keywords ***
Block Disabler
    Log    message
    # robocop: on=unused-variable
