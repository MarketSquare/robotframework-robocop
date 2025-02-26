*** Variables ***
# some comment

${VARIABLE 1}                           10    # comment
@{LIST}  a  b  c  d  # robotidy: off
${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes

# robotidy: off
           &{MULTILINE}  a=b
...  b=c
...         d=1
 ${invalid}
# robotidy: on
${invalid_more}

# should be left aligned
# should be left aligned
${variable}                             1