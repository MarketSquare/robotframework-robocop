*** Settings ***
Documentation      Here we have documentation for this suite.
...                Documentation is often quite long.
...
...               It can also contain multiple paragraphs.
Default Tags       default tag 1    default tag 2    default tag 3
...                default tag 4    default tag 5
Force Tags
...   tag
...    tag2


*** Variable ***
${STRING}          This is a long string.
...                It has multiple sentences.
...                It does not have newlines.
${MULTILINE}       SEPARATOR=\n
...                This is a long multiline string.
...               This is the second line.
...                This is the third and the last line.
@{LIST}            this     list     is      quite    long     and
...                 items in it can also be long
&{DICT}            first=This value is pretty long.
...                second=This value is even longer. It has two sentences.

*** Test Cases ***
Golden
    [Tags]    you    probably    do    not    have    this    many
    ...       tags    in    real    life
    Do X    first argument    second argument    third argument
    ...     fourth argument    fifth argument    sixth argument
    ${var} =    Get X
    ...    first argument passed to this keyword is pretty long
    ...    second argument passed to this keyword is long too

Test
    [Tags]    you    probably    do    not    have    this    many
    ...      tags    in    real    life
    Do X    first argument    second argument    third argument
    ...    fourth argument    fifth argument    sixth argument
    ...  misaligned argument
    ${var} =    Get X
    ...    first argument passed to this keyword is pretty long
    ...     second argument passed to this keyword is long too


*** Keywords ***
Misaligned Continuation
    [Arguments]    ${arg}
    ...   ${correct}
      ...  ${incorrect}
    Keyword
      ...  ${correct}
        ...  ${incorrect}
    Keyword With Misaligned Value
    ...  ${value}
    ...  2
    ...      ${value2}

Keyword With Documentation
    [Documentation]    This is my keyword documentation.
    ...
    ...   Arguments:
    ...       ${arg1}:      Value of arg1
    ...       ${arg2}:      Value of arg2
    No Operation
    ...  1
    ...   2
    ...    3

Keyword For 821 Bug
    Run Keywords
    ...    Log Message     1   AND
    # ...    Log Message     2   AND
    ...    Log Message     3   AND
# ...    Log Message     4   AND
    ...    Log Message     5

Keyword For 818 Bug
    ${arf}  Create List   1  2  3
    # ...  4
    ...  5
