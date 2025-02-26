*** Keywords ***
Keyword with [Return]

    No Operation
    RETURN    1  # it can be first

Keyword with Multiple [Return]
    Step 1
    Step 2
    RETURN    1



Keyword with RETURN
    No Operation
    RETURN    1

Keyword With Two RETURN
    IF    ${GLOBAL}    RETURN
    No Operation
    RETURN
