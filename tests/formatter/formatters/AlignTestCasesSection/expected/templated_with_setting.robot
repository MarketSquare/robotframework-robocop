*** Test Cases ***
Testing Random List
    [Template]              Validate Random List Selection
    # collection            nbr items
    ${SIMPLE LIST}          2
    ${MIXED LIST}           3
    ${NESTED LIST}          4
    ${SIMPLE LIST}          10
    ${MIXED LIST}           11
    ${NESTED LIST}          12

Testing Random Item
    [Template]              Validate Random Item Selection
    # collection
    ${SIMPLE LIST}
    ${MIXED LIST}
    ${NESTED LIST}

Testing Random Dict
    [Template]              Validate Random Dict Selection
    # collection            nbr items
    ${SIMPLE DICT}          2
    ${MIXED DICT}           3
    ${NESTED DICT}          4
    ${SIMPLE DICT}          10
    ${MIXED DICT}           11
    ${NESTED DICT}          12

Testing Random Sleep
    [Template]              Validate Random Sleep Duration
    # max expected          min delay               add delay
    1.1s                    1s                      ${EMPTY}                # Default Add Delay
    1.2s                    1s                      20%                     # Percentage Add Delay
    2s                      1s                      100%                    # Percentage Limits
    2.2s                    1s                      120%                    # Percentage Overlimit
    1.1s                    1.0                     1e-1                    # Number Format
    1.1s                    1s                      100ms                   # Time Format
    1.1s                    1000ms                  0.1                     # Mixed Format
    1s                      1s                      0                       # Zero additional Delay
    1s                      1s                      0%                      # Zero Percent

Testing Random Number
    [Template]              Validate Random Integer/Number Choice
    # method                min                     max
    number                  30e-10                  5.26                    # positive
    number                  26e3                    15                      # positive max under min
    number                  -18e0                   -2.2E0                  # negative
    number                  -26                     -28                     # negative max under min
    number                  ${{ - math.pi }}        ${{ math.e }}           # mixed
    number                  ${{ math.e }}           ${{ -math.tau }}        # mixed max under min
    number                  5.0                     5                       # no range

Testing Random Integer
    [Template]              Validate Random Integer/Number Choice
    # method                min                     max
    integer                 198564                  265489865               # positive
    integer                 3221564                 325                     # positive max under min
    integer                 -231                    -10                     # negative
    integer                 -2                      -212                    # negative max under min
    integer                 -56                     56                      # mixed
    integer                 23                      -15                     # mixed max under min
    integer                 -2                      -2                      # no range

Test Password Policy Minimum Length Input Errors
    [Documentation]    This Keyword Verifies Password Policy Minimum Length Input Errors
    [Tags]                  SERVICE-12345
    [Setup]                 Login With Random User
    [Teardown]              Test Teardown For User "${CURRENT_USER}"
    [Template]              Test Password Policy Minimum Length Error With Input
    ${SPACE}                Required
    5                       Invalid
    15                      Invalid
    0                       Invalid
    65.90                   Invalid
    hgsjaADC                Invalid
    $$ywu_%&#               Invalid
