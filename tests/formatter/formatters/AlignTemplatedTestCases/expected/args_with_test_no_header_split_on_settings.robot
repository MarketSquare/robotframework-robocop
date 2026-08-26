*** Settings ***
Test Template    Keyword

*** Test Cases ***
Without settings     arg1    arg2
Multiline no sett    arg1    arg2
                     arg3    arg4    arg5
With setting
    [Tags]    tag1    tag2
                     arg1    arg2
With doc
    [Documentation]    This is multiline doc, currently it affects alignment but I will ignore it in the future
                     arg1    arg2
New line
                     arg1
