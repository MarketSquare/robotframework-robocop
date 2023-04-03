*** Test Cases ***
My Test Case
    IF  ${condition}    Log  hello     ELSE    Log  hi!
    IF  ${condition}  Log  hello
  ...    ELSE       Log  hi!
    IF  ${condition}
        Log  hello
    ELSE
        Log  hi!
    END
    IF  ${condition}
    ...  Log  hello
    ...  ELSE
    ...  Log  hi!
    Log    something
    IF  ${condition}
    ...  Log  hello  ELSE  Log  hi!


*** Keywords ***
My Keyword
    IF  ${condition}    Log  hello     ELSE    Log  hi!
    IF  ${condition}  Log  hello
    ...    ELSE       Log  hi!
    IF  ${condition}
        Log  hello
    ELSE
        Log  hi!
    END
    IF  ${condition}
    ...  Log  hello
    ...  ELSE
    ...  Log  hi!
    Log    something
    IF  ${condition}
    ...  Log  hello  ELSE  Log  hi!
