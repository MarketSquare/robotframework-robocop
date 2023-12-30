*** Variables ***
{VAR_WITH_NO_TYPE}
${VAR_NO_VALUE}
@{LIST_NO_VALUE}
&{DICT_NO_VALUE}
@{LIST_NO_VALUE}
...
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
...
@{MULTILINE_EMPTY_WITH_COMMENT}   value
...    # I think it should be just empty line, without value - but I'm not sure
...    ${EMPTY}
@{MULTILINE_FIRST_EMPTY}
...
...  value
@{MULTILINE_WITH_MULTIPLE_EMPTIES}
...  1
...  2
...
...  a
...  b
...
...  3
${EMPTY_WITH_BACKSLASH}  \
@{MULTILINE_EMPTY_WITH_BACKSLASH}  \
...  \
@{MIXED_EMPTY}  \
...
...  ${EMPTY}
...  @{EMPTY}

... invalid
{also_invalid}  2
...


*** Keywords ***
VAR Syntax
    VAR    ${variable}    value
    VAR    ${variable}
    IF    ${variable}
        VAR    @{variable}
        VAR    &{variable}    scope=GLOBAL
    END
    VAR    $variable  # error
    VAR
    # VAR FIXME - uncomment after RF fix error (reported at https://github.com/robotframework/robotframework/issues/4995)
    # ...
    VAR    @{list}
    ...    value
    ...
    ...    scope=SUITE
    VAR
    ...    scope=local
