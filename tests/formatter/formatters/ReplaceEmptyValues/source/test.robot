*** Variables ***
${EMPTY_SCALAR}
${MULTILINE_SCALAR}
...
...    value2
${EMPTY_SCALAR_WITH_COMMENT}    # comment
${SCALAR}    value
@{EMPTY_LIST}
@{MULTILINE_LIST}
...    
...
...    value2
@{LIST_WITH_COMMENT}     # comment
...    # comment
...    value    # comment
@{ONELINE_LIST}    value1    value2
&{EMPTY_DICT}
&{MULTILINE_DICT}
...
...    key=value
&{DICT_WITH_COMMENT}    # comment
&{DICT}
...    key=value
...    key2=value
