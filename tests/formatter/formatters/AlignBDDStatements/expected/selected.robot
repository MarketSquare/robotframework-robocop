*** Test Cases ***
There can be only one
    Given there are 3 ninjas
      And there are more than one ninja alive
    When 2 ninjas meet, they will fight
    Then one ninja dies (but not me)
    And there is one ninja less alive

Only when and then
    When something happens
    Then result is expected

Not a BDD test
    Keyword Call
    Another Keyword    argument

Mixed with non BDD keywords
    Given precondition
    Log    message
    Then result is expected

Upper case prefixes
    GIVEN precondition
    WHEN action
    THEN result

With arguments and assignment
    Given keyword with argument    ${argument}
    ${variable} =    Given keyword with assignment
    Then result is expected

Already aligned
    Given precondition
      And another precondition
     Then result is expected
