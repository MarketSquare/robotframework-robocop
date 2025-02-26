*** Keywords ***
Keyword with [Return]
    [Return]    1  # it can be first

    No Operation

Keyword with Multiple [Return]
    [Return]    1
    Step 1
    Step 2



Keyword with RETURN
    No Operation
    RETURN    1

Keyword With Two RETURN
    IF    ${GLOBAL}    RETURN
    No Operation
    RETURN
