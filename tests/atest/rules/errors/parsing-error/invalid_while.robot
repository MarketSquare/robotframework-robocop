*** Test Cases ***
No condition
    [Documentation]    FAIL WHILE must have a condition.
    WHILE
        Fail    Not executed!
    END

Multiple conditions
    [Documentation]    FAIL WHILE cannot have more than one condition.
    WHILE    Too    many    !
        Fail    Not executed!
    END

No body
    [Documentation]    FAIL WHILE loop cannot be empty.
    WHILE    True
    END

No END
    [Documentation]    FAIL WHILE loop must have closing END.
    WHILE    True
        Fail    Not executed!
