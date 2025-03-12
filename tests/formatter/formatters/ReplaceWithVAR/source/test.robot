*** Test Cases ***
Set Variable
    ${local_variable}    Set Variable    value
    ${local_variable} =    Set Variable    value
    ${local_variable}=    Set Variable    value
    ${local_variable=    Set Variable    value  # invalid
    ${local_variable}=    ${local_variable}=    Set Variable    value  # invalid
    ${local_variable}    ${local_variable2}    Set Variable  # invalid
    ${local_variable}    Set Variable
    ${multiple_lines}    Set Variable
    ...    value
    ${comments}    Set Variable  # comment
    ...    value  # comment2
    ${multiple_values}    Set Variable   value1    value2

Set Variable with disablers
    ${local_variable}    Set Variable    value  # robocop: fmt: off
    ${list}    Create List
    ...  item
    ...  second item  # robocop: fmt: off
    ...  third item

Set Variable with scope
    # first declares, second de-scopes existing
    # for VAR, if not value given, we should repeat variable
    Set Local Variable    ${local_variable}    value
    Set Local Variable    ${local_variable}
    Set Task Variable    ${task_variable}    value
    Set Task Variable    ${task_variable}
    Set Test Variable    ${test_variable}    ${value}
    Set Test Variable    ${test_variable}
    Set Suite Variable    ${suite_variable}  # comment
    Set Suite Variable    ${suite_variable}    value with ${value}
    Set Suite Variable    ${suite_variable}    value1    value2
    Set Suite Variable    ${suite_variable}    value with ${value}    children=${True}  # ignored
    Set Global Variable    ${global_variable}    value
    Set Global Variable    ${global_variable}
    FOR    ${var}    IN    @{list}
        Set Suite Variable    @LIST      First item       Second item
        Set Suite Variable    &DICT      key=value        foo=bar
        Set Suite Variable    $SCALAR    ${EMPTY}
        IF    ${condition}
            Set Suite Variable    @LIST      @{EMPTY}
            Set Suite Variable    &DICT      &{EMPTY}
            Set Suite Variable    $SCALAR
        ELSE
            Set Suite Variable    @LIST
            Set Suite Variable    &DICT
        END
    END

Escaped variables
    Set Global Variable    $variable
    Set Suite Variable    \${variable}
    Set Task Variable    @variable
    Set Test Variable    \&{variable}

Set Variable with list
    @{list}    Set Variable    value    value2
    @{list}    Set Variable    value

Multiple Set Variable
    ${var1}    ${var2}    Set Variable    value    value2
    ${var1}    ${var2}    Set Variable    value  # runtime error
    ${var1}    ${var2}    Set Variable    @{list}

Create List
    ${scalar}    Create List    a    b
    @{list}    Create List    a    ${1}
    ...    ${2}
    IF    ${condition}
        ${empty_list}    Create List
    END
    ${empty_values}    Create List
    ...    a
    ...
    ...    c
    ${first_list}    ${second_list}    Create List    value  # invalid
    ${first_list}    ${second_list}    Create List    value    value  # valid but does not return list

Create Dictionary
    ${dict}    Create Dictionary    key=value
    TRY
        &{dict}    Create Dictionary    key=value
    EXCEPT
        No Operation
    END
    ${dict}    Create Dictionary
    ${dict}=    Create Dictionary    key=value
    ...    key2=value  # comment
    ${dict}    Create Dictionary    key=value
    ...
    ...    key2=value
    ${dict}    Create Dictionary    key    value
    ${dict}    Create Dictionary    key    value    key2     value
    ${dict}    Create Dictionary    key    value    key2
    ${dict}    Create Dictionary    ${1}=${2}    &{dict}    foo=new
    ${dict}    Create Dictionary   key=value    separate    value

Catenate
    ${string}    Catenate    join  with  spaces
    ${string}    BuiltIn.Catenate    SEPARATOR=${SPACE}    join  with  spaces
    ${string}=  Catenate    SEPARATOR=,   comma  separated  list
    Catenate    No  Assign
    ${string}    Catenate   single ${value}
    ${multiline_with_empty}    Catenate    value
    ...
    ...   third value
    Catenate
    Catenate    SEPARATOR=\n
    ${assign}    Catenate    separator=${SPACE}
    ${assign}    Catenate    SEPARATOR=${SPACE}
    ${assign}    Catenate    first    SEPARATOR=${SPACE}
    ${assign}    Catenate    SEPARATOR=    first
    ${assign}    Catenate    first    SEPARATOR=

Set Variable If
    ${var1} =    Set Variable If    ${rc} == 0    zero    nonzero
    ${var2}    Set Variable If    ${rc} > 0    value1    value2
    ${var3} =    Set Variable If    ${rc} > 0    whatever
    ${var}=    Set Variable If    ${rc} == 0    zero
    ...    ${rc} > 0    greater than zero    less then zero
    ${var}    Set Variable If    ${condition}    @{items}
    ${var}    Set Variable If

Inline IF
    ${value}    IF    ${condition}    Set Variable    value    ELSE    Set Variable    ${None}  # comment
    ${value}    IF    ${condition}    Set Variable    value    ELSE IF  False    BuiltIn.Set Variable    value2    ELSE    Set Variable    ${None}

Inline IF mixed set variable and custom keyword
    ${value}    IF    ${condition}    Set Variable    value    ELSE IF  False    Custom Keyword    ELSE    Set Variable    ${None}

Inline IF set with one assign and one arg
    ${value}    IF    ${condition}    Set Variable    value

Inline IF set with one assign no args
    ${value}    IF    ${condition}    Set Variable

Inline IF set with two assign two args
    ${many}    ${vars}    IF    True   Set Variable    value    value

Inline IF set with two assign one arg
    ${many}    ${vars}    IF    True   Set Variable    value

Inline IF set if and custom keyword value2
    # ELSE belongs to IF, and it cannot be converted to inline if
    ${assign}    IF    ${rc} > 0    Set Variable If  ${rc}==1  value1  ELSE  value2

Inline IF set if with else value2
    # second value is ELSE value
    ${assign}    IF    ${rc} > 0    Set Variable If  ${rc}==1  value1  value2

Inline IF set scope
    IF    ${condition}    Set Suite Variable    ${value}    ELSE    Set Global Variable    ${value}    default
    IF    ${condition}    Set Suite Variable    ${value}    ELSE    VAR    ${value}    default
    IF    ${condition}    Set Suite Variable    ${value}    ELSE    Custom Keyword    default

Inline IF invalid
    IF    ${condition}    VAR    ${value}    value    ELSE    Set Variable    ${value}    value  # invalid
    ${assign}    IF    ${condition}    Set Suite Variable    ${value}    ELSE    Set Global Variable    ${value}    default

Inline IF without set
    ${assign}    IF    Custom Keyword  ${arg}  ELSE  Custom Keyword 2

Inline IF with statements
    IF    ${condition}    Set Task Variable    ${value}    ELSE    RETURN
    IF    ${condition}    Set Task Variable    ${value}    ELSE IF    False    BREAK    ELSE    CONTINUE

VAR
    VAR    ${variable}    already there

Other keywords
    No Operation
    ${var}    Set Custom Variable
