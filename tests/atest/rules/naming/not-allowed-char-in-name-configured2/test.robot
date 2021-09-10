*** Keywords ***
Perform A ${arg:\d+} ${arg2:\d+}
    Log To Console  ${arg}. ${arg2}

Perform ABCD ${arg:\d+} ${arg2:\d+}
    Log To Console  ${arg}. ${arg2}

Perform ${arg:.*}
    Log To Console  ${arg}
