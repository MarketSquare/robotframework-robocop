*** Test Cases ***
Adjacent IF
    No Operation
    IF  ${condition} == 'True'
        Step 1
    END
    # comment
    IF  ${condition} == 'True'
        Step 2
    END

Not adjacent
    IF  ${condition} == 'True'
        Step 1
    END
    No Operation
    IF  ${condition} == 'True'
        Step 2
    END

Different conditions
    IF  ${condition} == 'True'
        Step 1
    END
    IF  ${condition} == 'False'
        Step 2
    END

Mixed conditions
    IF  ${condition} == 'True'
        Step 1
    END
    IF  ${condition} == 'False'
        Step 2
    END
    IF  ${condition} == 'True'
        Step 3
    END

Nested Adjacent If
    IF  ${condition} == 'True'
        Step 1
        IF  ${STUFF}
            Log  Oh!
        END
    END



    IF  ${condition} == 'True'
        Step 2
    END

Single nested If
    IF  ${condition} == 'True'
        Step 1
        IF  ${condition} == 'True'
            Log  Oh!
        END
    END

Adjacent inside for loop
    FOR  ${value}  IN RANGE  10
        IF  ${value}==${5}
            Log    ${value}
        END
        IF  ${value}==${5}
            Log    ${value}
        END
    END
    IF  ${value}==${5}
        Log    ${value}
    END

Adjacent but with comment
    IF  ${condition} == 'True'
        Step 1
    END
    IF  ${condition} == 'True'  # comment
        Step 2
    END

*** Keywords ***
Adjacent IF
    No Operation
    IF  ${condition} == 'True'
        Step 1
    END
    # comment
    IF  ${condition} == 'True'
        Step 2
    END

Adjacent inside IF
    IF  ${condition} == 'True'
        IF  ${condition} == 'True'
            Step 1
        END
        IF  ${condition} == 'True'
            Step 2
        END
    END

ElSE IF not adjacent
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    END
    IF  ${condition} == 'True'
        Step 2
    END

ELSE IF not adjacent similar branches
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    END
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff2}
        Step 2
    END

ELSE IF not adjacent similar branches 2
    IF  ${condition} == 'True'
        Step 1  ${argument}
    ELSE IF  ${stuff}
        Step 2
    END
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    ELSE
       Step 3
    END

ELSE IF adjacent
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    ELSE
        Step 3
    END
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    ELSE
       Step 4
    END

Three identical if
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    END
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    END
    IF  ${condition} == 'True'
        Step 1
    ELSE IF  ${stuff}
        Step 2
    END

Adjacent but in different RF5 TRY EXCEPT blocks
    TRY
        IF  ${condition} == 'True'
            Step 1
        ELSE IF  ${stuff}
            Step 2
        END
    EXCEPT
        IF  ${condition} == 'True'
            Step 1
        ELSE IF  ${stuff}
            Step 2
        END
    END
