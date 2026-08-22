*** Test Cases ***
Disabled statements
    Given there are 3 ninjas  # robocop: fmt: off
    And there are more than one ninja alive  # robocop: fmt: off
    When 2 ninjas meet, they will fight  # robocop: fmt: off=AlignBDDStatements

# robocop: fmt: off
Disabled block
    Given there are 3 ninjas
    And there are more than one ninja alive
# robocop: fmt: on
