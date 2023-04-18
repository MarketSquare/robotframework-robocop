*** Settings ***
Test Template


*** Test Cases ***
Test without template
    No Operation

Test with non-empty template
    [Template]    Template
    argument

Test with empty template
    [Template]
    No Operation

Test with empty template and NONE
    [Template]    NONE
    No Operation
