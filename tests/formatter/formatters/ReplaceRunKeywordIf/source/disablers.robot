*** Test Cases ***
Leave existing if blocks
    IF    condition
        Keyword
    ELSE IF  condition2
        Keyword2
    ELSE
        Keyword
    END

Single Return Value
    ${var}  Run Keyword If  ${condition}  Keyword With ${var}  ${arg}  # robocop: fmt: off

Multiple Return Values
    # robocop: fmt: off
    ${var}  ${var2}  Run Keyword If  ${condition}  Keyword With ${var}  ${arg}

Run keyword if with else if
    Run Keyword If  ${condition}    Keyword
    ...  ELSE IF  ${other_condition}    Other Keyword  # robocop: fmt: off
    ...  ELSE  Final Keyword
# robocop: fmt: off
Run keyword if with else if and args
    Run Keyword If  ${condition}    Keyword  a  b  c
    ...  ELSE IF  ${other_condition}    Other Keyword
    ...  ELSE  Final Keyword  1  2  ${var}

Run keyword if with else if and return values
    ${var}  ${var}  Run Keyword If  ${condition}    Keyword
    ...  ELSE IF  ${other_condition}    Other Keyword  ${arg}
    ...  ELSE  Final Keyword

Run keyword if with else if and run keywords
    Run Keyword If  "${var}"=="a"    Run Keywords  First Keyword  AND  Second Keyword  1  2
    ...  ELSE IF  ${var}==1  Run Keywords  Single Keyword  ${argument}
    ...  ELSE  Normal Keyword  abc
# robocop: fmt: on
Run keyword if inside FOR loop
    FOR  ${var}  IN  @{elems}
        Run Keyword If  ${condition}    Keyword
        ...  ELSE IF  ${other_condition}    Other Keyword  # robocop: fmt: off
        ...  ELSE  Final Keyword
    END
# robocop: fmt: off
Run keyword if inside IF
    IF  ${condition}
        Run Keyword If  ${condition}    Keyword
        ...  ELSE IF  ${other_condition}    Other Keyword
        ...  ELSE  Final Keyword
    END

*** Keywords ***
# robocop: fmt: off
Test Content Merged Into One Keyword
    IF    condition
        Keyword
    ELSE IF  condition2
        Keyword2
    ELSE
        Keyword
    END

    Run Keyword If  ${condition}    Keyword
    ...  ELSE IF  ${other_condition}    Other Keyword
    ...  ELSE  Final Keyword

    Run Keyword If  ${condition}    Keyword  a  b  c
    ...  ELSE IF  ${other_condition}    Other Keyword
    ...  ELSE  Final Keyword  1  2  ${var}

    ${var}  ${var}  Run Keyword If  ${condition}    Keyword
    ...  ELSE IF  ${other_condition}    Other Keyword  ${arg}
    ...  ELSE  Final Keyword

    Run Keyword If  "${var}"=="a"    Run Keywords  First Keyword  AND  Second Keyword  1  2
    ...  ELSE IF  ${var}==1  Run Keywords  Single Keyword  ${argument}
    ...  ELSE  Normal Keyword  abc

Empty
    Run Keyword If
# robocop: fmt: on
With BuiltIn
    ${var}    BuiltIn.Run Keyword If    ${condition}    Keyword    ELSE    Set Variable  ${1}  # robocop: fmt: off
