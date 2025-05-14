*** Variables ***
${VARIABLE}    value_
${VAR_IABLE}    ${VA_LUE}
${VARIABLE}    This is string with ${VARIABLE}
${${VAR}}    value
${VARIABLE}    ${${VARIABLE}}
${VARIABLE}    ${VAR_${VARIABLE}_VAR}
${VARIABLE}    String with ${${variable}}  # robocop: fmt: off
${VARIABLE}    ${VARIABLE['item_access']}
${VARIABLE}    ${VARIABLE}[item_access]
${VARIABLE}    ${VARIABLE}[${ITEM}_access]
${VARIABLE}    ${_}____
${VARI_ABLE}    ${WO_RD}
${VARIABLE}     \${escaped}

&{DICT}    item=value
...    item=${VALUE}
@{LIST}    value
...    other ${VALUE}
...    ${{embedd_ ed}

${CAMEL_CASE_NAME}    ${CAMEL_CASE_NAME}
${CAMEL_CASE_NAME}    ${CAMEL_CASE_NAME}
${CAMEL_CASE_NAME}    ${CAMEL_CASE_NAME}
${CAMEL_CASE_NAME_WORD_CAMEL_CASE}    ${CAMEL_CASE_NAME_WORD_CAMEL_CASE}


*** Test Cases ***
Assign
    ${variable}    Keyword
    FOR    ${var}    IN    1  2
        # robocop: fmt: off=NormalizeNewLines, RenameVariables
        ${MULTIPLE}
        ...   ${variables }    Keyword
    END
    ${variable} =    Keyword
    ${variable}=    Keyword

Args
    Keyword    ${VARIABLE}
    Keyword    ${v a _riAbles}  # robocop: fmt: off = RenameVariables
    ...    value with ${_ variable _}

Arguments
    [Arguments]    ${arg}   # TODO
    Step

# globals
# embedded
# FOR ${var}
# settings