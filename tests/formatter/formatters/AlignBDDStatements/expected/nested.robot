*** Test Cases ***
Test with nested blocks
    Given precondition
    IF    ${condition}
        When action
         And another action
    ELSE
        Given other precondition
         Then other result
    END
     Then final result

Test with for loop
    Given precondition
    FOR    ${index}    IN RANGE    3
        When action ${index}
         And another action
        Then result ${index}
    END
     Then final result
