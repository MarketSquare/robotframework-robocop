*** Settings ***
Documentation  doc  #invalid comment
Metadata   myvalue  #invalid comment
Force Tags  sometag  #invalid comment
Default Tags  mytag  #invalid comment
Test Setup      Keyword  #invalid comment
Test Teardown   Keyword  #invalid comment
Suite Setup     Keyword  #invalid comment
Suite Teardown  Keyword  #invalid comment
Test Template   Keyword  #invalid comment


*** Variables ***
${MY_VAR}    1  #invalid comment  with 2 spaces


*** Test Cases ***  # valid comment
Test  #invalid comment
    [Documentation]  doc  # valid comment
    [Tags]  sometag  #invalid comment
    [Setup]  Keyword  #invalid comment
    [Template]  Keyword  #invalid comment
    [Timeout]  10  #invalid comment
    Pass
    Keyword  # valid comment
    One More
#invalid comment

*** Keywords ***  #invalid comment
Keyword  #invalid comment
    [Documentation]  this is doc  #invalid comment
    [Arguments]  ${arg}  #invalid comment
    [Timeout]  10  #invalid comment
    No Operation  #invalid comment
    Pass
    No Operation
    Fail
    IF  ${var}  #invalid comment
        My Keyword
    ELSE IF  ${another_var}  #invalid comment
        Not My Keyword
    ELSE  #invalid comment
        Banned Keyword
    END
    FOR  ${var}  IN  @{list}  #invalid comment
        My Keyword
    END
    [Return]  ${val}  #invalid comment

RF 5 syntax
    WHILE    $condition  #invalid comment
        TRY  #invalid comment
            Keyword
        EXCEPT  #invalid comment
            Keyword
        FINALLY  #invalid comment
            Keyword
        ELSE  #invalid comment
            Keyword
        END  #invalid comment
        CONTINUE  #invalid comment
        BREAK  #invalid comment
    END

Double comments
    # valid  still valid  with 2 spaces
    # valid  ## valid
    ########### block comments #########
    Keyword  # valid  still valid  with 2 spaces
    Keyword  # valid  ## valid
