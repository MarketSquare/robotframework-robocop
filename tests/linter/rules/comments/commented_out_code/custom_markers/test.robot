*** Keywords ***
Keyword With Custom Markers
    # NOTE: ${var}=    this should be ignored with custom markers
    # SKIP: [Tags]    smoke
    # ${result}=    this should be reported
    # TODO: ${other}=    Get Value
    Log    Done
