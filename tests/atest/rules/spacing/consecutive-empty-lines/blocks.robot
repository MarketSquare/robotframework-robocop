*** Settings ***
Resource    ../../misc/if-can-be-merged/test.robot
*** Keywords ***
FOR Loop
    FOR    ${var}    IN RANGE    10

        Log    ${var}


        No Operation
    END

Consecutive between FOR loops
    FOR    ${var}    IN RANGE    10
        No Operation
    END


    FOR    ${var}    IN RANGE    10
        No Operation
    END

IF block
    IF    ${condition}


        No Operation


        No Operation
        No Operation


    ELSE IF    $flag


        No Operation


        No Operation
        No Operation


    ELSE


        No Operation


        No Operation
        No Operation


    END

Inline IF
    IF    ${condition}    Keyword


    IF    ${condition}    Keyword

WHILE Loop
    WHILE    ${condition}


            No Operation


            No Operation


    END

TRY EXCEPT
    TRY


            No Operation


            No Operation


    EXCEPT    *


            No Operation


            No Operation


    FINALLY


            No Operation


            No Operation


    ELSE


            No Operation


            No Operation


    END
