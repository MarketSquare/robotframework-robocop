*** Settings ***
Library    ExampleLibrary    @{lib_args}
Library    ${library}    @{lib_args}

Variables    ${name}.py
Resource    ${curdir}/${name}.robot

Suite Setup    Some Keyword    @{kw_ARGS}
Suite Teardown    ${Keyword}    @{KW_ARGS}
Test Setup    Some Keyword    @{kw_ARGS}
Test Teardown    ${Keyword}    @{KW_ARGS}

Default Tags    @{tags}    tag_${name}
Test Timeout    ${timeout}

Metadata  ${item}    ${value}


*** Variables ***
${VARIABLE}    value_
${VAR_IABLE}    ${VA_LUE}
${VARIABLE}    This is string with ${VARIABLE}
${${VAR}}    value
${VARIABLE}    ${${VARIABLE}}
${VARIABLE}    ${VAR_${VARIABLE}_VAR}
${VARIABLE}    String with ${${VARIABLE}}
${VARIABLE}    ${VARIABLE['item_access']}
${VARIABLE}    ${VARIABLE}[item_access]
${VARIABLE}    ${VARIABLE}[${ITEM}_access]
${VARIABLE}    ${VARIABLE['${VARIABLE}']}
${VARIABLE}    ${_}____
${VARI_ABLE}    ${WO_RD}
${VARIABLE}     \${escaped}
${INLINE_EVAL}    ${{ eval }}

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
    ${multiple}
    ...   ${variables}    Keyword
    ${variable} =    Keyword
    ${variable}=    Keyword
    Keyword  ${NESTED_${variable}}

Args
    Keyword    ${VARIABLE}
    Keyword    ${V_A_RI_ABLES}
    ...    value with ${VARIABLE}

For header
    ${local}    Set Variable    item
    FOR    ${item}    IN    @{LIST}
        Log    ${item}
        Do Stuff    String with ${local} value
        ...    ${lo_cal}  # TODO We could normalize it to look as first local matching variable
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
    [Tags]    ${var}    tag with ${var}
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

Embedded ${arguments} that ${should_be_lower} and also ${pattern:\S}
    Log    ${should_be_lower}
    Log    ${GLOBAL}
    Log    ${pattern}

Multiple underscores
    Log    ${MY_VAR_NESTED_VAR_1_NESTED_VAR_2}
