*** Variables ***
${GLOBAL}    global


*** Keywords ***
Not named
    ${local}    Keyword Call
    GROUP
        Keyword Call    ${LOCAL}
        ${local_from_group}    Keyword Call    ${global}
    END
    Keyword Call    ${LOCAL_FROM_GROUP}

Named with variable
    GROUP    Name with ${global}
        Keyword Call
    END
    GROUP    Nested
        VAR    ${local}    local
        GROUP    Named with ${LOCAL}
            Keyword Call
        END
    END
