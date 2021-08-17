*** Variables ***
${VAR_NO_VALUE}
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
${MULTILINE_WITH_EMPTY_LINES}   Value
...    # I think it should be just empty line, without value - but I'm not sure
...    ${EMPTY}
