*** Variables ***
${EMPTY_SCALAR}    ${EMPTY}
${MULTILINE_SCALAR}
...    ${EMPTY}
...    value2
${EMPTY_SCALAR_WITH_COMMENT}    ${EMPTY}    # comment
${SCALAR}    value
@{EMPTY_LIST}    @{EMPTY}
@{MULTILINE_LIST}
...    ${EMPTY}
...    ${EMPTY}
...    value2
@{LIST_WITH_COMMENT}     # comment
...    ${EMPTY}    # comment
...    value    # comment
@{ONELINE_LIST}    value1    value2
&{EMPTY_DICT}    &{EMPTY}
&{MULTILINE_DICT}
...
...    key=value
&{DICT_WITH_COMMENT}    &{EMPTY}    # comment
&{DICT}
...    key=value
...    key2=value
