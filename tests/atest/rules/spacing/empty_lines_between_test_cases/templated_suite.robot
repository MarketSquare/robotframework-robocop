*** Settings ***
Suite Setup      Create Authenticated Service Session
Suite Teardown   Close Ascentis Service Session
Test Template    Get Novatime Service Request Template


*** Test Cases ***                   ${arg1}           ${arg2}
Get Accrual Details for Paycode 1    1                 1
Get Accrual Details for Paycode 2    2                 2
Get Accrual Details for Paycode 3    3                 3
Get Accrual Details for Paycode 4    4                 4
Get Accrual Details for Paycode 5    5                 5
# comment
Get Accrual Details for Paycode 6    6                 6

Get Accrual Details for Paycode 7    7                 7


Get Accrual Details for Paycode 8    8                 8
