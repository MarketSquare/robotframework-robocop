*** Settings ***
Force Tags    PS_CSMON_15838    PR_PPD    PR_B450
...           PR_B650    PR_B850    PR_CS1000
...           PR_CS1000L    PAR_ECG    PAR_IP_1
...           PAR_SPO2


*** Variables ***    # variables are not aligned but it will be handled by AlignVariablesSection
@{LIST}
...    valuevaluevaluevaluevalue
...    valuevaluevaluevaluevalue
...    valuevaluevaluevaluevalue


*** Test Cases ***
Testcase with a lot of tags
    [Tags]    Tag1    Tag10    Tag11    Tag12
    ...       Tag13    Tag2    Tag3    Tag4
    ...       Tag5    Tag6    Tag7    Tag8    Tag9
    ...       Tag14    Tag15
    Fail


*** Keywords ***
Keyword
    Keyword With Longer Name    ${arg1}    ${arg2}
    ...                         ${arg3}

Keyword Longer Than Limit
    This Keyword Goes Beyond Limit And Next Argument Should Be In New Line
    ...    ${arg}
