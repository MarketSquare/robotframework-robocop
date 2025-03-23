*** Test Cases ***
Template arguments are local scope
    [Template]    My Keyword ${embedded_arg}
    value1
    value2

Upper Case argument will be converted to lower case
    [Template]    My Keyword ${arg}
    value1
    value2


*** Keywords ***
Keyword Argument Is Also ${embedded_arg} Local Scope
    Log To Console    embedded arg: ${embedded_arg}
