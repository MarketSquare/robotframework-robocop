*** Settings ***
Library    ExampleLibrary    @{LIB ARGS}
Library    ${LIBRARY}    @{LIB ARGS}

Variables    ${NAME}.py
Resource    ${CURDIR}/${NAME}.robot

Suite Setup    Some Keyword    @{KW ARGS}
Suite Teardown    ${KEYWORD}    @{KW ARGS}
Test Setup    Some Keyword    @{KW ARGS}
Test Teardown    ${KEYWORD}    @{KW ARGS}

Default Tags    @{TAGS}    tag_${NAME}
Test Timeout    ${TIMEOUT}

Metadata  ${ITEM}    ${VALUE}


*** Variables ***
${VARIABLE}    value_
${VAR IABLE}    ${VA LUE}
${VARIABLE}    This is string with ${VARIABLE}
${${VAR}}    value
${VARIABLE}    ${${VARIABLE}}
${VARIABLE}    ${VAR ${VARIABLE} VAR}
${VARIABLE}    String with ${${VARIABLE}}
${VARIABLE}    ${VARIABLE['item_access']}
${VARIABLE}    ${VARIABLE}[item_access]
${VARIABLE}    ${VARIABLE}[${ITEM}_access]
${VARIABLE}    ${VARIABLE['${VARIABLE}']}
${VARIABLE}    ${_}____
${VARI ABLE}    ${WO RD}
${VARIABLE}     \${escaped}
${INLINE EVAL}    ${{ eval }}

&{DICT}    item=value
...    item=${VALUE}
@{LIST}    value
...    other ${VALUE}
...    ${{embedd_ ed}

${CAMEL CASE NAME}    ${CAMEL CASE NAME}
${CAMEL CASE NAME}    ${CAMEL CASE NAME}
${CAMEL CASE NAME}    ${CAMEL CASE NAME}
${CAMEL CASE NAME WORD CAMEL CASE}    ${CAMEL CASE NAME WORD CAMEL CASE}


*** Test Cases ***
Assign
    ${variable}    Keyword
    ${multiple}
    ...   ${variables}    Keyword
    ${variable} =    Keyword
    ${variable}=    Keyword
    Keyword  ${NESTED ${variable}}

Args
    Keyword    ${VARIABLE}
    Keyword    ${V A RI ABLES}
    ...    value with ${VARIABLE}

For header
    ${local}    Set Variable    item
    FOR    ${item}    IN    @{LIST}
        Log    ${item}
        Do Stuff    String with ${local} value
        ...    ${lo cal}  # TODO We could normalize it to look as first local matching variable
    END
    Log    ${GLOBAL}
    Log    ${item}
    FOR    ${index}    ${item}    IN ENUMERATE    @{LIST}
         Log    ${index}    ${item}
    END
    Log    ${local['item']}
    Log    ${GLOBAL['item']}

Test With Variables In Keyword Call
    [Setup]    ${KEYWORD}
    ${local}    Set Variable    local value
    Keyword Call With ${VARIABLE}
    Keyword Call With ${local}
    ${global}    Keyword Call With ${GLOBAL}
    [Teardown]    ${local}

Test case with ${VARIABLE} in name
    [Documentation]    The RF surprises me vol. 678
    Step

Test with variables in tags
    [Tags]    ${VAR}    tag with ${VAR}
    Step


*** Keywords ***
Arguments
    [Arguments]    ${arg}    ${arg2}
    Step    ${arg}
    Step    ${ARG3}

Kwargs
    [Arguments]    ${arg}    &{kwargs}
    Step

Defaults
    [Arguments]    ${arg}    ${arg2} = 'default'
    Step

Defaults With Global
    [Arguments]    ${arg}    ${arg2} =${GLOBAL}
    Step

Defaults With Other Arg
    [Arguments]    ${arg}    ${arg2} = ${arg}
    Step

Embedded ${arguments} that ${should be lower} and also ${pattern:\S}
    Log    ${should be lower}
    Log    ${GLOBAL}
    Log    ${pattern}

Multiple underscores
    Log    ${MY VAR NESTED VAR 1 NESTED VAR 2}
