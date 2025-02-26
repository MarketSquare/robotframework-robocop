*** Variables ***
&{USER_PROFILE}
...    name=John Doe
...    age=12
...    hobby=coding
@{VERY_LONG_VARIABLE_NAME_CONTAINING_FRUITS}
...    apple
...    banana
...    pineapple
...    tomato
${NO_VALUE}

error

# comment
${SCALAR}
...    with
...    comment
...    value
...    value

*** Variables ***
# comment1
# comment2
# comment3
# comment4                              with extra words
# comment5
@{LIST}
...    value
...    ${EMPTY}
...    value2
...    value3
...    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
...    looooooooooooooooooooooooooooooooooooooooong

${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
@{LONG_WITH_SINGLE}
...    short
...    short
...    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
