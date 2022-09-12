*** Settings ***
Test Template  My Nice Template

*** Test Cases ***
Templated Test With Documentation
    [Documentation]  doc
    ARG1  ARG2
    ARG1  ARG3  # another test

Templated Test Without Documentation
    ARG1  ARG2
    ARG1  ARG3  # another test

Overriding Default Template In Test Without Documentation
    [Template]  Better Template
    ARG1  ARG2
    ARG1  ARG4

Overriding Default Template In Test With Documentation
    [Template]  Better Template
    [Documentation]  Some cool documentation
    ARG1  ARG2
    ARG1  ARG4

Template With FOR Loop Containing Variables
    [Tags]    42   # tags are fine
    FOR    ${item}    IN    a    b    @{TEST TAGS}
        ${VARIABLE}    ${item}
    END

Strange Test With Docs In One Line    [Documentation]    Short docs    ARG1    ARG2
Strange Test Without Docs In One Line    ARG1    ARG2
