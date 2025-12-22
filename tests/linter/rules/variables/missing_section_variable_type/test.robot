*** Variables ***
# Should report - no type
${NUMBER}    42
@{LIST}      one    two
&{DICT}      key=value

# Should NOT report - has type
${TYPED_NUMBER: int}    42
@{TYPED_LIST: str}      one    two
&{TYPED_DICT: str=int}  key=1

# Should report - colon without space (embedded pattern, not type annotation)
${NO_SPACE:pattern}    value

# Should NOT report - ignore variables
${_}         ignored
${_unused}   ignored

# Negative tests - invalid syntax, should NOT report and not throw exceptions
${var}
...    val
 ....    val
value

&{dict}    1

# Multiline variable
${MULTILINE}
...    line1
...    line2


*** Keywords ***
Keyword With VAR
    VAR    ${local}    value
    VAR    ${typed_local: str}    value
    VAR    ${_ignored}    value
    Log    ${local} ${typed_local}

Keyword With Multiline VAR
    VAR
    ...    ${multiline_var}
    ...    value
    VAR
    ...    ${typed_multiline: str}
    ...    value
    Log    ${multiline_var} ${typed_multiline}

Keyword With Assignment
    ${result} =    Set Variable    value
    ${typed_result: list} =    Create List    one    two
    ${_ignored} =    Set Variable    value
    Log    ${result} ${typed_result}
