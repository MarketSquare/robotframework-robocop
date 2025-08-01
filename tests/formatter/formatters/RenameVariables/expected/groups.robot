*** Variables ***
${GLOBAL}    global


*** Keywords ***
Not named
    ${local}    Keyword Call
    GROUP
        Keyword Call    ${local}
        ${local_from_group}    Keyword Call    ${GLOBAL}
    END
    Keyword Call    ${local_from_group}

Named with variable
    GROUP    Name with ${GLOBAL}
        Keyword Call
    END
    GROUP    Nested
        VAR    ${local}    local
        GROUP    Named with ${local}
            Keyword Call
        END
    END
