*** Settings ***
Force Tags    PS_CSMON_15838    PR_PPD    PR_B450    PR_B650    PR_B850    PR_CS1000    PR_CS1000L    PAR_ECG
...    PAR_IP_1    PAR_SPO2
Default Tags    PS_CSMON_15838    PR_PPD    PR_B450    PR_B650    PR_B850    PR_CS1000    PR_CS1000L    PAR_ECG
...    PAR_IP_1    PAR_SPO2
# comment


*** Test Cases ***
Test with lots of tags
    [Tags]    PS_CSMON_15838    PR_PPD    PR_B450    PR_B650    PR_B850    PR_CS1000    PR_CS1000L    PAR_ECG
    ...    PAR_IP_1    PAR_SPO2
    Prepare
    Run
    Assert

Test with comments in settings
    [Tags]    tag    tag    PS_CSMON_15838    PR_PPD    PR_B450    PR_B650    PR_B850    PR_CS1000    PR_CS1000L
    ...    PAR_ECG    PAR_IP_1    PAR_SPO2
    # comment1
    # comment2
    # comment3


*** Keywords ***
Arguments
    [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    Step

Arguments multiline
    [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    Step

Arguments single line over limit
    [Arguments]    ${short}
    ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLengthveryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    Step

Comment that goes over the allowed length
    [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
    # this is long comment and it should be ignored with --skip-comments
    Step

Invalid arguments
   [Arguments]    ${Multiline_Argument1}    ${Multiline_Argument2}    ${Multiline_Argument3}    ${Multiline_Argument4}
                    ${Multiline_Argument5}    ${Multiline_Argument6}    ${Multiline_Argument7}    ${Multiline_Argument8}
    ...    ${Multiline_Argument9}    ${Multiline_Argument10}    ${Multiline_Argument11}    ${Multiline_Argument12}
    ...    ${Multiline_Argument13}    ${Multiline_Argument14}    ${Multiline_Argument15}    ${Multiline_Argument16}
   [Documentation]    Missing continuation line.
