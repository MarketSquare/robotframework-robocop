*** Test Cases ***
Template arguments are local scope
    [Template]    My Keyword ${embedded arg}
    value1
    value2

Upper Case argument will be converted to lower case
    [Template]    My Keyword ${ARG}
    value1
    value2


*** Keywords ***
Keyword Argument Is Also ${embedded arg} Local Scope
    Log To Console    embedded arg: ${embedded arg}
