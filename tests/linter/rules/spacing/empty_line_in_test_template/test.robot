*** Settings ***
Test Template    Template Keyword


*** Test Cases ***
Suite template
    first

    second


Multiple ignored lines
    first

    
    third


Commented groups
    first

    # This comment and the blank lines around it are meaningful.

    second


Multiline data
    first
    ...    continued

    second


Locally disabled template
    [Template]    NONE
    First Keyword

    Second Keyword


Nested control structures
    FOR    ${item}    IN    first    second
        loop first

        loop second

        # This comment and the blank lines around it are meaningful.

        loop third
        IF    $condition
            if first

            if second
        ELSE
            else first

            else second
        END
    END
