*** Settings ***
Documentation    doc.

# robocop: off=rule1

Test Timeout    1 min

# robocop: off

*** Test Cases ***
No disabler
    No Operation

# robocop: off=rule2
Enable inside test should not enable higher scope disabler
    No Operation
    # robocop: on
    No Operation

Disablers in blocks
    FOR    ${var}    IN    1  2
        # robocop: off=rule3
        IF    $var
            # robocop: off=rule4
            Log    ${var}
        ELSE
            Log    not ${var}
        END
    END
    WHILE    ${TRUE}
        No Operation
        # robocop: off=rule2
        TRY
            Process Value
        EXCEPT
            # robocop: on
            Log    Except
        ELSE
            # robocop: off=rule1
        END
    END

*** Keywords ***
No disabler
    No Operation

# robocop: off=rule2
Enable inside test should not enable higher scope disabler
    No Operation
    # robocop: on
    No Operation

Disablers in blocks
    FOR    ${var}    IN    1  2
        # robocop: off=rule3
        IF    $var
            # robocop: off=rule4
            Log    ${var}
        ELSE
            Log    not ${var}
        END
    END
    WHILE    ${TRUE}
        No Operation
        # robocop: off=rule2
        TRY
            Process Value
        EXCEPT
            # robocop: on
            Log    Except
        ELSE
            # robocop: off=rule1
        END
    END
