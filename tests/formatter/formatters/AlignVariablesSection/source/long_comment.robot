*** Variables ***
# some comment that is longer than usual and can go and go and ends     here

${VARIABLE 1}  10  # comment
@{LIST}  a  b  c  d
${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes

           &{MULTILINE}  a=b
...  b=c
...         d=1
 ${invalid}
  ${invalid_more}