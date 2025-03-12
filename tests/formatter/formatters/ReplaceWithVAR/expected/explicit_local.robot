*** Test Cases ***
Set Variable
    VAR    ${local_variable}    value    scope=LOCAL
    VAR    ${local_variable}    value    scope=LOCAL
    VAR    ${local_variable}    value    scope=LOCAL
    ${local_variable=    Set Variable    value  # invalid
    ${local_variable}=    ${local_variable}=    Set Variable    value  # invalid
    ${local_variable}    ${local_variable2}    Set Variable  # invalid
    VAR    ${local_variable}    ${EMPTY}    scope=LOCAL
    VAR    ${multiple_lines}    value    scope=LOCAL
    # comment
    # comment2
    VAR    ${comments}    value    scope=LOCAL
    VAR    @{multiple_values}    value1    value2    scope=LOCAL

Set Variable with disablers
    ${local_variable}    Set Variable    value  # robocop: fmt: off
    ${list}    Create List
    ...  item
    ...  second item  # robocop: fmt: off
    ...  third item

Set Variable with scope
    # first declares, second de-scopes existing
    # for VAR, if not value given, we should repeat variable
    VAR    ${local_variable}    value    scope=LOCAL
    VAR    ${local_variable}    ${local_variable}    scope=LOCAL
    VAR    ${task_variable}    value    scope=TASK
    VAR    ${task_variable}    ${task_variable}    scope=TASK
    VAR    ${test_variable}    ${value}    scope=TEST
    VAR    ${test_variable}    ${test_variable}    scope=TEST
    VAR    ${suite_variable}    ${suite_variable}    scope=SUITE  # comment
    VAR    ${suite_variable}    value with ${value}    scope=SUITE
    VAR    @{suite_variable}    value1    value2    scope=SUITE
    Set Suite Variable    ${suite_variable}    value with ${value}    children=${True}  # ignored
    VAR    ${global_variable}    value    scope=GLOBAL
    VAR    ${global_variable}    ${global_variable}    scope=GLOBAL
    FOR    ${var}    IN    @{list}
        VAR    @{LIST}    First item    Second item    scope=SUITE
        VAR    &{DICT}    key=value    foo=bar    scope=SUITE
        VAR    ${SCALAR}    ${EMPTY}    scope=SUITE
        IF    ${condition}
            VAR    @{LIST}    @{EMPTY}    scope=SUITE
            VAR    &{DICT}    &{EMPTY}    scope=SUITE
            VAR    ${SCALAR}    ${SCALAR}    scope=SUITE
        ELSE
            VAR    @{LIST}    @{LIST}    scope=SUITE
            VAR    &{DICT}    &{DICT}    scope=SUITE
        END
    END

Escaped variables
    VAR    ${variable}    ${variable}    scope=GLOBAL
    VAR    ${variable}    ${variable}    scope=SUITE
    VAR    @{variable}    @{variable}    scope=TASK
    VAR    &{variable}    &{variable}    scope=TEST

Set Variable with list
    VAR    @{list}    value    value2    scope=LOCAL
    VAR    @{list}    value    scope=LOCAL

Multiple Set Variable
    VAR    ${var1}    value    scope=LOCAL
    VAR    ${var2}    value2    scope=LOCAL
    ${var1}    ${var2}    Set Variable    value  # runtime error
    ${var1}    ${var2}    Set Variable    @{list}

Create List
    VAR    @{scalar}    a    b    scope=LOCAL
    VAR    @{list}    a    ${1}    ${2}    scope=LOCAL
    IF    ${condition}
        VAR    @{empty_list}    @{EMPTY}    scope=LOCAL
    END
    VAR    @{empty_values}    a    ${EMPTY}    c    scope=LOCAL
    ${first_list}    ${second_list}    Create List    value  # invalid
    ${first_list}    ${second_list}    Create List    value    value  # valid but does not return list

Create Dictionary
    VAR    &{dict}    key=value    scope=LOCAL
    TRY
        VAR    &{dict}    key=value    scope=LOCAL
    EXCEPT
        No Operation
    END
    VAR    &{dict}    &{EMPTY}    scope=LOCAL
    VAR    &{dict}    key=value    key2=value    scope=LOCAL  # comment
    ${dict}    Create Dictionary    key=value
    ...
    ...    key2=value
    VAR    &{dict}    key=value    scope=LOCAL
    VAR    &{dict}    key=value    key2=value    scope=LOCAL
    VAR    &{dict}    key=value    key2    scope=LOCAL
    VAR    &{dict}    ${1}=${2}    &{dict}    foo=new    scope=LOCAL
    VAR    &{dict}    key=value    separate    value    scope=LOCAL

Catenate
    VAR    ${string}    join    with    spaces    scope=LOCAL    separator=${SPACE}
    VAR    ${string}    join    with    spaces    scope=LOCAL    separator=${SPACE}
    VAR    ${string}    comma    separated    list    scope=LOCAL    separator=,
    Catenate    No  Assign
    VAR    ${string}    single ${value}    scope=LOCAL    separator=${SPACE}
    VAR    ${multiline_with_empty}    value    ${EMPTY}    third value    scope=LOCAL    separator=${SPACE}
    Catenate
    Catenate    SEPARATOR=\n
    VAR    ${assign}    separator=${SPACE}    scope=LOCAL    separator=${SPACE}
    VAR    ${assign}    ${EMPTY}    scope=LOCAL    separator=${SPACE}
    VAR    ${assign}    first    SEPARATOR=${SPACE}    scope=LOCAL    separator=${SPACE}
    VAR    ${assign}    first    scope=LOCAL    separator=${EMPTY}
    VAR    ${assign}    first    SEPARATOR=    scope=LOCAL    separator=${SPACE}

Set Variable If
    IF    ${rc} == 0
        VAR    ${var1}    zero    scope=LOCAL
    ELSE
        VAR    ${var1}    nonzero    scope=LOCAL
    END
    IF    ${rc} > 0
        VAR    ${var2}    value1    scope=LOCAL
    ELSE
        VAR    ${var2}    value2    scope=LOCAL
    END
    IF    ${rc} > 0
        VAR    ${var3}    whatever    scope=LOCAL
    ELSE
        VAR    ${var3}    ${None}    scope=LOCAL
    END
    IF    ${rc} == 0
        VAR    ${var}    zero    scope=LOCAL
    ELSE IF    ${rc} > 0
        VAR    ${var}    greater than zero    scope=LOCAL
    ELSE
        VAR    ${var}    less then zero    scope=LOCAL
    END
    ${var}    Set Variable If    ${condition}    @{items}
    ${var}    Set Variable If

Inline IF
    IF    ${condition}
        VAR    ${value}    value    scope=LOCAL
    ELSE
        VAR    ${value}    ${None}    scope=LOCAL  # comment
    END
    IF    ${condition}
        VAR    ${value}    value    scope=LOCAL
    ELSE IF    False
        VAR    ${value}    value2    scope=LOCAL
    ELSE
        VAR    ${value}    ${None}    scope=LOCAL
    END

Inline IF mixed set variable and custom keyword
    IF    ${condition}
        VAR    ${value}    value    scope=LOCAL
    ELSE IF    False
        ${value}    Custom Keyword
    ELSE
        VAR    ${value}    ${None}    scope=LOCAL
    END

Inline IF set with one assign and one arg
    IF    ${condition}
        VAR    ${value}    value    scope=LOCAL
    END

Inline IF set with one assign no args
    IF    ${condition}
        VAR    ${value}    ${EMPTY}    scope=LOCAL
    END

Inline IF set with two assign two args
    IF    True
        VAR    ${many}    value    scope=LOCAL
        VAR    ${vars}    value    scope=LOCAL
    END

Inline IF set with two assign one arg
    ${many}    ${vars}    IF    True   Set Variable    value

Inline IF set if and custom keyword value2
    # ELSE belongs to IF, and it cannot be converted to inline if
    IF    ${rc} > 0
        IF    ${rc}==1
            VAR    ${assign}    value1    scope=LOCAL
        ELSE
            VAR    ${assign}    ${None}    scope=LOCAL
        END
    ELSE
        ${assign}    value2
    END

Inline IF set if with else value2
    # second value is ELSE value
    IF    ${rc} > 0
        IF    ${rc}==1
            VAR    ${assign}    value1    scope=LOCAL
        ELSE
            VAR    ${assign}    value2    scope=LOCAL
        END
    END

Inline IF set scope
    IF    ${condition}
        VAR    ${value}    ${value}    scope=SUITE
    ELSE
        VAR    ${value}    default    scope=GLOBAL
    END
    IF    ${condition}
        VAR    ${value}    ${value}    scope=SUITE
    ELSE
        VAR    ${value}    default
    END
    IF    ${condition}
        VAR    ${value}    ${value}    scope=SUITE
    ELSE
        Custom Keyword    default
    END

Inline IF invalid
    IF    ${condition}    VAR    ${value}    value    ELSE    Set Variable    ${value}    value  # invalid
    ${assign}    IF    ${condition}    Set Suite Variable    ${value}    ELSE    Set Global Variable    ${value}    default

Inline IF without set
    ${assign}    IF    Custom Keyword  ${arg}  ELSE  Custom Keyword 2

Inline IF with statements
    IF    ${condition}
        VAR    ${value}    ${value}    scope=TASK
    ELSE
        RETURN
    END
    IF    ${condition}
        VAR    ${value}    ${value}    scope=TASK
    ELSE IF    False
        BREAK
    ELSE
        CONTINUE
    END

VAR
    VAR    ${variable}    already there

Other keywords
    No Operation
    ${var}    Set Custom Variable
