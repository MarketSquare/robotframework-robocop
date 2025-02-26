*** Settings ***
Library    ExampleLibrary    @{lib_args}
Library    ${library}    @{lib_args}

Variables    ${name}.py
Resource    ${curdir}/${name}.robot

Suite Setup    Some Keyword    @{kw_args}
Suite Teardown    ${keyword}    @{kw_args}
Test Setup    Some Keyword    @{kw_args}
Test Teardown    ${keyword}    @{kw_args}

Default Tags    @{tags}    tag_${name}
Test Timeout    ${timeout}

Metadata  ${item}    ${value}


*** Variables ***
${variable}    value_
${var_iable}    ${va_lue}
${variable}    This is string with ${variable}
${${VAR}}    value
${variable}    ${${variable}}
${variable}    ${var_${variable}_var}
${variable}    String with ${${variable}}
${variable}    ${variable['item_access']}
${variable}    ${variable}[item_access]
${variable}    ${variable}[${item}_access]
${variable}    ${variable['${variable}']}
${variable}    ${_}____
${vari_able}    ${wo_rd}
${variable}     \${escaped}
${inline_eval}    ${{ eval }}

&{dict}    item=value
...    item=${value}
@{list}    value
...    other ${value}
...    ${{embedd_ ed}

${camel_case_name}    ${camel_case_name}
${camel_case_name}    ${camel_case_name}
${camel_case_name}    ${camel_case_name}
${camel_case_name_word_camel_case}    ${camel_case_name_word_camel_case}


*** Test Cases ***
Assign
    ${variable}    Keyword
    ${multiple}
    ...   ${variables}    Keyword
    ${variable} =    Keyword
    ${variable}=    Keyword
    Keyword  ${nested_${variable}}

Args
    Keyword    ${variable}
    Keyword    ${v_a_ri_ables}
    ...    value with ${variable}

For header
    ${local}    Set Variable    item
    FOR    ${item}    IN    @{list}
        Log    ${item}
        Do Stuff    String with ${local} value
        ...    ${lo_cal}  # TODO We could normalize it to look as first local matching variable
    END
    Log    ${global}
    Log    ${item}
    FOR    ${index}    ${item}    IN ENUMERATE    @{list}
         Log    ${index}    ${item}
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
    Step    ${arg3}

Kwargs
    [Arguments]    ${arg}    &{kwargs}
    Step

Defaults
    [Arguments]    ${arg}    ${arg2} = 'default'
    Step

Defaults With Global
    [Arguments]    ${arg}    ${arg2} =${global}
    Step

Defaults With Other Arg
    [Arguments]    ${arg}    ${arg2} = ${arg}
    Step

Embedded ${arguments} that ${should_be_lower} and also ${pattern:\S}
    Log    ${should_be_lower}
    Log    ${global}
    Log    ${pattern}

Multiple underscores
    Log    ${my_var_nested_var_1_nested_var_2}
