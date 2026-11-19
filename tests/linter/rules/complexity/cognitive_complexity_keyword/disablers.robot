*** Keywords ***
Deep But Allowed    # robocop: off=cognitive-complexity-keyword
    FOR    ${i}    IN RANGE    3
        IF    $i == 1    Log    1
        IF    $i == 2    Log    2
        IF    $i == 3    Log    3
        IF    $i == 4    Log    4
        IF    $i == 5    Log    5
        IF    $i == 6    Log    6
        IF    $i == 7    Log    7
        IF    $i == 8    Log    8
        IF    $i == 9    Log    9
        IF    $i == 10    Log    10
    END
