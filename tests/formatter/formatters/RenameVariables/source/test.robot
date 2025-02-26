*** Settings ***
Library    ExampleLibrary    @{lib args}
Library    ${library}    @{lib args}

Variables    ${name}.py
Resource    ${curdir}/${name}.robot

Suite Setup    Some Keyword    @{kw ARGS}
Suite Teardown    ${Keyword}    @{KW ARGS}
Test Setup    Some Keyword    @{kw ARGS}
Test Teardown    ${Keyword}    @{KW ARGS}

Default Tags    @{tags}    tag_${name}
Test Timeout    ${timeout}

Metadata  ${item}    ${value}


*** Variables ***
${variable_}    value_
${var_iable_}    ${va lue}
${VARIABLE}    This is string with ${variable}
${${VAR}}    value
${VARIABLE}    ${${variable}}
${VARIABLE}    ${var_${variable}_var}
${VARIABLE}    String with ${${variable}}
${VARIABLE}    ${variable['item_access']}
${VARIABLE}    ${variable}[item_access]
${VARIABLE}    ${variable}[${item}_access]
${VARIABLE}    ${variable['${variable}']}
${VARIABLE__}    ${___}____
${VARI_ ABLE}    ${wo_ rd}
${VARIABLE}     \${escaped}
${INLINE_EVAL}    ${{ eval }}

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
    ${MULTIPLE}
    ...   ${variables }    Keyword
    ${variable} =    Keyword
    ${variable}=    Keyword
    Keyword  ${nested_${variable}}

Args
    Keyword    ${variable }
    Keyword    ${v a _riAbles}
    ...    value with ${_ variable _}

For header
    ${local}    Set Variable    item
    FOR    ${ITEM}    IN    @{list}
        Log    ${ITEM}
        Do Stuff    String with ${LOCAL} value
        ...    ${lo_CAL}  # TODO We could normalize it to look as first local matching variable
    END
    Log    ${global}
    Log    ${ITEM}
    FOR    ${INDEX}    ${ITEM}    IN ENUMERATE    @{LIST}
         Log    ${INDEX}    ${ITEM}
    END
    Log    ${local['item']}
    Log    ${global['item']}

Test With Variables In Keyword Call
    [Setup]    ${keyword}
    ${local}    Set Variable    local value
    Keyword Call With ${variable}
    Keyword Call With ${local}
    ${global}    Keyword Call With ${global}
    [Teardown]    ${local}

Test case with ${variable} in name
    [Documentation]    The RF surprises me vol. 678
    Step

Test with variables in tags
    [Tags]    ${var}    tag with ${var}
    Step


*** Keywords ***
Arguments
    [Arguments]    ${arg}    ${ARG2}
    Step    ${arg}
    Step    ${arg3}

Kwargs
    [Arguments]    ${arg}    &{KWARGS}
    Step

Defaults
    [Arguments]    ${arg}    ${ARG2} = 'default'
    Step

Defaults With Global
    [Arguments]    ${arg}    ${ARG2} =${global}
    Step

Defaults With Other Arg
    [Arguments]    ${arg}    ${ARG2} = ${arg}
    Step

Embedded ${arguments} that ${SHOULD_BE_LOWER} and also ${pattern:\S}
    Log    ${should_be lower}
    Log    ${global}
    Log    ${pattern}

Multiple underscores
    Log    ${MY_VAR__NESTED_VAR_1__NESTED_VAR_2}
