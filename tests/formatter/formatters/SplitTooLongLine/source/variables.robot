*** Variables ***
&{USER_PROFILE}                   name=John Doe                            age=12                            hobby=coding
@{VERY_LONG_VARIABLE_NAME_CONTAINING_FRUITS}             apple    banana    pineapple    tomato
${NO_VALUE}

error

${SCALAR}    with   comment                                value                             value    # comment

*** Variables ***
# comment1
@{LIST}  # comment2
...  value  # comment3
...  # comment4                              with extra words
...  value2  value3  # comment5
...  veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery    looooooooooooooooooooooooooooooooooooooooong

${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
@{LONG_WITH_SINGLE}
...    short    short
...    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
