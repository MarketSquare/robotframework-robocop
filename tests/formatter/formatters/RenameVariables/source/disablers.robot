*** Variables ***
${variable_}    value_
${var_iable_}    ${va lue}
${VARIABLE}    This is string with ${variable}
${${VAR}}    value
${VARIABLE}    ${${variable}}
${VARIABLE}    ${var_${variable}_var}
${VARIABLE}    String with ${${variable}}  # robocop: fmt: off
${VARIABLE}    ${variable['item_access']}
${VARIABLE}    ${variable}[item_access]
${VARIABLE}    ${variable}[${item}_access]
${VARIABLE__}    ${___}____
${VARI_ ABLE}    ${wo_ rd}
${VARIABLE}     \${escaped}

&{dict}    item=value
...    item=${value}
@{list}    value
...    other ${ value}
...    ${{embedd_ ed}

${camelCaseName}    ${camelCaseName}
${CamelCaseName}    ${CamelCaseName}
${camelCASEName}    ${camelCASEName}
${camelCASEName_word_camelCase}    ${camelCASEName_WORD_camelCase}


*** Test Cases ***
Assign
    ${ variable}    Keyword
    FOR    ${var}    IN    1  2
        # robocop: fmt: off=NormalizeNewLines, RenameVariables
        ${MULTIPLE}
        ...   ${variables }    Keyword
    END
    ${variable} =    Keyword
    ${Variable}=    Keyword

Args
    Keyword    ${variable }
    Keyword    ${v a _riAbles}  # robocop: fmt: off = RenameVariables
    ...    value with ${_ variable _}

Arguments
    [Arguments]    ${arg}   # TODO
    Step

# globals
# embedded
# FOR ${var}
# settings