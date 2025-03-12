*** Variables ***
${VARIABLE}    value


*** Keywords ***
No Arguments
    ${value}    Keyword Call    ${VARIABLE}

Used Arguments
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}    ${arg7}
    ${value}    Set Variable    ${a_rg1}
    IF    $arg2    RETURN
    IF    $arg3 == 2    RETURN
    IF    $arg5 != '${arg6}' and $arg7
        Log    Mixed syntax
    END
    Set Global Variable    \${arg4}    value

Not Used Arguments
    [Arguments]    ${arg1}    ${arg2}
    ${value}    Set Variable    ${arg 1}

Overwritten Argument
    [Arguments]    ${arg1}    ${overwritten1}    ${overwritten2}    ${overwritten3}    ${overwritten_but_used}
    ${overwritten1}    Set Variable    ${arg1}
    ${overwritten2}    Set Variable    ${arg1}
    ${overwritten_but_used}    Keyword    String with ${overwritten_but_used}
    Keyword Call    ${overwritten1}  # used, but by overwritten
    Keyword Call    ${overwritten2}  # used, but by overwritten
    FOR    ${overwritten3}    IN    @{arg1}
        Log    ${overwritten3}
    END

Argument In String
    [Arguments]    ${used}    ${not_used}
    Keyword Call
    ...    Sentence with ${used} argument

Nested Arguments
    [Arguments]    ${used}    ${used2}    ${not_used}
    Keyword Call    ${name_${used}}
    Keyword Call    ${variable}[${used2}]

Args And Kwargs
    [Arguments]    ${arg1}    @{arg2}    &{arg3}
    ${value}    Set Variable    ${arg1}

Embedded ${argument} and ${argument2}
    Keyword Call    ${ARGUMENT}

Embedded ${argument:pattern} and ${argument2}
    WHILE    $argument
        No Operation
    END

Used In For
    [Arguments]    ${for_arg}
    FOR    ${item}    IN    @{for_arg}
        No Operation
    END

Overwritten In Try As
    [Arguments]    ${error}    ${used}
    TRY
        Do Stuff
    EXCEPT    Error    AS    ${error}
        Log    ${error}
    FINALLY
        Keyword    ${used}
    END

Arguments With Defaults
    [Arguments]    ${var}='default'    ${var2}=2
    Log    ${var2}

Ignored Error
    [Arguments]    ${not_used}  # robocop: off=unused-argument
    Log    It shall not be reported.

Escaped In Keyword
    [Arguments]    ${traceback}    ${stacktrace}
    ${error} =    Set Variable If    $traceback and not $stacktrace
    ...    ${error}\nTraceback (most recent call last):\n*${traceback}*
    ...    ${error}

Inline Eval
    [Arguments]    ${starttime}
    Element Attribute Should Be       ${elem}    timestamp
    ...    ${{datetime.datetime.strptime($starttime, '%Y%m%d %H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S.%f')}}

Dot Syntax
    [Arguments]    ${kw}    ${model_object}
    Log    ${kw.attr}
    Should Not Be True     ${model_object.setup}

Attribute Access
    [Arguments]    ${object}    ${text}
    Should Contain    ${object['doc']}    ${text}

Attribute Access 2
    [Arguments]    ${test}    @{files}
    FOR    ${index}    ${file}    IN ENUMERATE    @{files}
        Check Log Message    ${test.kws[0].msgs[${index}]}    ${file}
    END

Argument In [Return]
    [Arguments]    ${var}
    [Return]    ${var}${SPACE * ${padding}}| ${status} |

Argument In [RETURN]
    [Arguments]    ${var}
    RETURN    ${var}

Argument In Teardown
    [Arguments]    ${tests}    ${server}    ${stop server}=yes
    ${port} =    Start Remote Server    ${server}
    Run Tests    --variable PORT:${port}    standard_libraries/remote/${tests}
    [Teardown]    Run Keyword If    '${stop server}' == 'yes'
    ...    Stop Remote Server    ${server}

Argument In Timeout
    [Arguments]   ${timeout}
    [Timeout]    ${timeout}
    Sleep    0.1

Embedded \${?} error
    No Operation

Embedded${? error
    No Operation

IF With Assign
    [Arguments]    ${arg}
    ${arg}    IF    $arg    Keyword

Keyword Call With Variable Error
    [Arguments]    ${used}
    Keyword Call    String with ${variable
    Log    ${used}

Empty Condition Or Var
    [Arguments]    ${used}
    WHILE
        No Operation
    END
    IF
        No Operation
    END
    FOR    In    1  2
        No Operation
    END
    TRY
        Keyword
    EXCEPT  AS
    END
    Log    ${used}

Errors In Arguments
    [Arguments]    ${argument} = value
    Log    ${argument}

While Limit
    [Arguments]    ${used_arg}    ${used_arg2}
    WHILE    $condition    limit=${used_arg}
        Log    In loop.
    END
    WHILE    ${used_arg2}
        Log    In loop.
    END

Variable Used Next to Other
    [Arguments]    ${file_location}
    Log To Console    message=${file_location}${/}filename

Prepare Item With Attribute
    ${item}    Get Item
    ${item.x}    Set Variable    abc
    RETURN    ${item}

Update Item With Attribute
    ${item}    Get Item
    ${item.x}    Set Variable    abc

Use Item With Attribute
    ${item}    Prepare Item
    Log    ${item.x}

Use Item With Method
    ${string}    Set Variable    string
    ${lower_string}    Set Variable    ${string.lower()}
    Log    ${lower_string}

Used In String Literal
    [Arguments]    ${used}    ${unused}
    Log  ${used} unused

Loop Header From Arguments And Global Count
    [Arguments]    ${list}
    FOR    ${item}    IN    @{list}
        Set To Dictionary    ${item}    displayOrder=${count}
        ${count}    Evaluate    ${count} + 1
    END

Overwritten in VAR
    [Arguments]    ${arg1}    ${overwritten1}    ${overwritten2}    ${overwritten_but_used}
    VAR    ${overwritten1}    ${arg1}
    VAR    ${overwritten2}    ${arg1}
    VAR    ${overwritten_but_used}    String with ${overwritten_but_used}
    Keyword Call    ${overwritten1}  # used, but overwritten before
    Keyword Call    ${overwritten2}  # used, but overwritten before

Used In Other Argument
    [Arguments]    ${argument}    ${argument2}=default with ${argument}
    Log    ${argument2}

Used In For While Option
    [Arguments]    ${start}    ${limit}    ${condition}    @{list}
    FOR    ${index}    ${value}    IN ENUMERATE    @{list}    start=${start}
        Log Many    ${index}    ${value}
    END
    WHILE    ${condition}    limit=${limit}
        No Operation
    END

Used in EXCEPT branch
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}    ${arg7}
    TRY
        May Fail    ${arg1}
    EXCEPT    ${arg2}
        No Operation
    EXCEPT    ${arg3}    ${arg4}
        No Operation
    EXCEPT    Error    AS    ${arg5}  # used variable, overwrites, should raise overwrite of unused
        Use    ${arg5}
    EXCEPT    Error    AS    ${arg6}  # unused variable, overwrites, should raise overwrite of unused
        No Operation
    END
    TRY
        Some Keyword
    EXCEPT    ValueError: .*    type=${arg7}
        No Operation
    END
