*** Settings ***
Documentation    doc.

# robocop: disable=rule1

Test Timeout    1 min

# robocop: disable

*** Test Cases ***
No disabler
    No Operation

# robocop: disable=rule2
Enable inside test should not enable higher scope disabler
    No Operation
    # robocop: enable
    No Operation

Disablers in blocks
    FOR    ${var}    IN    1  2
        # robocop: disable=rule3
        IF    $var
            # robocop: disable=rule4
            Log    ${var}
        ELSE
            Log    not ${var}
        END
    END
    WHILE    ${TRUE}
        No Operation
        # robocop: disable=rule2
        TRY
            Process Value
        EXCEPT
            # robocop: enable
            Log    Except
        ELSE
            # robocop: disable=rule1
        END
    END

*** Keywords ***
No disabler
    No Operation

# robocop: disable=rule2
Enable inside test should not enable higher scope disabler
    No Operation
    # robocop: enable
    No Operation

Disablers in blocks
    FOR    ${var}    IN    1  2
        # robocop: disable=rule3
        IF    $var
            # robocop: disable=rule4
            Log    ${var}
        ELSE
            Log    not ${var}
        END
    END
    WHILE    ${TRUE}
        No Operation
        # robocop: disable=rule2
        TRY
            Process Value
        EXCEPT
            # robocop: enable
            Log    Except
        ELSE
            # robocop: disable=rule1
        END
    END
