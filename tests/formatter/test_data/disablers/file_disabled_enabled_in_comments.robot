*** Comments ***
# robocop: fmt: off

Some comments that should not be formatted

# fmt: on


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
