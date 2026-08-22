*** Keywords ***
All Calls Wrapped
    Run Keyword And Continue On Failure    Assert A
    Run Keyword And Continue On Failure    Assert B
    BuiltIn.Run Keyword And Continue On Failure    Assert C

Not Wrapped
    Assert A
    Assert B
