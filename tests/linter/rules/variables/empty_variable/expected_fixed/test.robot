*** Variables ***
{VAR_WITH_NO_TYPE}
${VAR_NO_VALUE}    ${EMPTY}
@{LIST_NO_VALUE}    @{EMPTY}
&{DICT_NO_VALUE}    &{EMPTY}
@{LIST_NO_VALUE}
...    ${EMPTY}
&{DICT_NO_VALUE}
...
${VAR_WITH_EMPTY}       ${EMPTY}
@{VAR_WITH_EMPTY}       @{EMPTY}
&{VAR_WITH_EMPTY}       &{EMPTY}
${VAR_WITH_VALUE}       Value
${VAR_WITH_INT}         ${1}
${VAR_WIH_STR}          1
${VAR_WITH_LIST}        one     two     three
${MULTILINE_WITH_EMPTY}
...    ${EMPTY}
${MULTILINE_NO_VALUE}
...    ${EMPTY}
@{MULTILINE_EMPTY_WITH_COMMENT}   value
...    ${EMPTY}    # I think it should be just empty line, without value - but I'm not sure
...    ${EMPTY}
@{MULTILINE_FIRST_EMPTY}
...    ${EMPTY}
...  value
@{MULTILINE_WITH_MULTIPLE_EMPTIES}
...  1
...  2
...    ${EMPTY}
...  a
...  b
...    ${EMPTY}
...  3
${EMPTY_WITH_BACKSLASH}  ${EMPTY}
@{MULTILINE_EMPTY_WITH_BACKSLASH}  ${EMPTY}
...  ${EMPTY}
@{MIXED_EMPTY}  ${EMPTY}
...    ${EMPTY}
...  ${EMPTY}
...  @{EMPTY}

... invalid
{also_invalid}  2
...


*** Keywords ***
VAR Syntax
    VAR    ${variable}    value
    VAR    ${variable}    ${EMPTY}
    IF    ${variable}
        VAR    @{variable}    @{EMPTY}
        VAR    &{variable}    &{EMPTY}    scope=GLOBAL
    END
    VAR    $variable  # error
    VAR
    # VAR FIXME - uncomment after RF fix error (reported at https://github.com/robotframework/robotframework/issues/4995)
    # ...
    VAR    @{list}
    ...    value
    ...    ${EMPTY}
    ...    scope=SUITE
    VAR
    ...    scope=local
