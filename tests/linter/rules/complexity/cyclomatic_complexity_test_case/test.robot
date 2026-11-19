*** Test Cases ***
Simple Test
    Log    hello

Eight Branches Test
    IF    $a == 1    Log    1
    IF    $a == 2    Log    2
    IF    $a == 3    Log    3
    IF    $a == 4    Log    4
    IF    $a == 5    Log    5
    IF    $a == 6    Log    6
    IF    $a == 7    Log    7

Many Branches Test
    IF    $a == 1    Log    1
    IF    $a == 2    Log    2
    IF    $a == 3    Log    3
    IF    $a == 4    Log    4
    IF    $a == 5    Log    5
    IF    $a == 6    Log    6
    IF    $a == 7    Log    7
    IF    $a == 8    Log    8
    IF    $a == 9    Log    9
    IF    $a == 10    Log    10


*** Keywords ***
Simple Keyword
    Log    hello

Many Legacy Branches
    Run Keyword If    $a == 1    Log    1
    Run Keyword If    $a == 2    Log    2
    Run Keyword If    $a == 3    Log    3
    Run Keyword If    $a == 4    Log    4
    Run Keyword If    $a == 5    Log    5
    Run Keyword If    $a == 6    Log    6
    Run Keyword If    $a == 7    Log    7
    Run Keyword If    $a == 8    Log    8
    Run Keyword If    $a == 9    Log    9
    Run Keyword If    $a == 10    Log    10

Mixed Branches
    IF    $mode == 'a'
        Log    a
    ELSE IF    $mode == 'b'
        Log    b
    ELSE IF    $mode == 'c'
        Log    c
    ELSE
        Log    other
    END
    FOR    ${item}    IN    @{items}
        IF    $item == 1    CONTINUE
        IF    $item == 2    BREAK
        IF    $item == 3    Log    three
    END
    TRY
        Risky Keyword
    EXCEPT    ValueError*    type=glob
        Log    value error
    EXCEPT
        Log    other error
    END
    Skip If    $skip
    WHILE    $retry    limit=3
        Log    retry
    END

Ten Decisions
    FOR    ${item}    IN    @{items}
        IF    $item == 1    Log    1
        IF    $item == 2    Log    2
        IF    $item == 3    Log    3
        IF    $item == 4    Log    4
        IF    $item == 5    Log    5
        IF    $item == 6    Log    6
        IF    $item == 7    Log    7
        IF    $item == 8    Log    8
    END

Suppressed Keyword    # robocop: off
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
