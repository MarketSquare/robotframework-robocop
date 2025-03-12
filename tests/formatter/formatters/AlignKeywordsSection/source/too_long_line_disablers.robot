*** Keywords ***
Many arguments
    # fits without alignment
    Keyword    argument1    argument2    argument3    argument4    argument5    argument6    argument7    argument8

    # does not fit before alignment
    Longer Keyword Name That Could Happen In Real Life Too    argument value with sentence that goes over the characters limit  # robocop: fmt: off=SplitTooLongLine,AlignKeywordsSection

    # multiline but fits without alignment
    Keyword
    ...    arg
    ...    argument1    argument2    argument3    argument4    argument5    argument6    argument7    argument8

Many assignments
    # robocop: fmt: off=AlignKeywordsSection,all
    ${longer_argument}    ${longer_argument2}    ${longer_argument3}    ${longer_argument4}    ${longer_argument5}    ${longer_argument6}    Keyword
    ...    argument1    argument2
