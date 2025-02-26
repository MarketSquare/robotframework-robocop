*** Variables ***
# some comment

${VARIABLE 1}       10                  # comment
@{LIST}             a                   b                   c                   d
${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes

&{MULTILINE}        a=b
...                 b=c
...                 d=1
${invalid}
${invalid_more}

# should be left aligned
# should be left aligned
${variable}         1