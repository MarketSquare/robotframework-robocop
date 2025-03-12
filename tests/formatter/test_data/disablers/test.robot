*** Settings ***
Library  SeleniumLibrary

Metadata    Key    Value

*** Test Cases ***
Test
    [Documentation]     This is doc
    Step
    FOR    ${var}    IN RANGE    10
        IF    $condition
            WHILE    ${arg}
                ${return}    Keyword    ${value}
                ...    ${other_value}    # robocop: fmt: off
            END
        ELSE IF
            Step    ${arg}
            ...    value
            Step 2
            #  comment
        END
    END

*** Keywords ***
# robocop: fmt: off
Keyword
    [Arguments]    ${arg}
    # robocop: fmt: on
    Step
    # robocop: fmt: off
    Step  1
    ...  2

Keyword 2
    No Operation

# fmt: on

Keyword 3
    [Tags]    tag
    ...   tag2    # robocop: fmt: off
    WHILE    $condition
        FOR    ${var}   IN  1  2
            IF    $var
                Step
                # robocop: fmt: off
                Step 2
                # robocop: fmt: on
                IF    $var
                    ${return}    Step 3    a    b
                END
            ELSE IF
                TRY
                    Step
                EXCEPT
                    Step
                    # robocop: fmt: off
                    Step 2
                ELSE
                    Step
                FINALLY
                    Step
                END
            END
        END

    FOR    ${var}    IN    a  b  # robocop: fmt: off
        Keyword    ${var}
    END
