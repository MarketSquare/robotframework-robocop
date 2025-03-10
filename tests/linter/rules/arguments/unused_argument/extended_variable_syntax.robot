*** Keywords ***
Extended Variable Syntax
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}
    Log    ${arg1 + "test"}    level=warn
    Log    ${arg2 * 3}    level=warn
    Log    ${arg3[1]}    level=warn
    Log    ${arg4 == "test"}
    Log    ${arg5 == arg6}
