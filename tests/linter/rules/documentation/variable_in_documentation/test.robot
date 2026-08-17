*** Settings ***
Documentation       Defined scalar ${SCALAR} and undefined ${UNDEFINED}.
...                 Defined list @{LIST}, dictionary &{DICT}, and environment %{ROBOCOP_DOC_ENV}.
...                 Escaped literals \${SCALAR}, \@{LIST}, \&{DICT}, and \%{ROBOCOP_DOC_ENV}.
...                 Literal example: Log    ${message}

*** Variables ***
${SCALAR}           value
@{LIST}             first    second
&{DICT}             key=value

*** Test Cases ***
Variable syntax in test documentation
    [Documentation]    Scalar ${test scalar}.
    ...                List @{test list}, dictionary &{test dict}, environment %{TEST_ENV}.
    ...                Escaped \${test scalar}, \@{test list}, \&{test dict}, \%{TEST_ENV}.
    No Operation

*** Keywords ***
Variable syntax in keyword documentation
    [Documentation]    Scalar ${keyword scalar}.
    ...                List @{keyword list}, dictionary &{keyword dict}, environment %{KEYWORD_ENV}.
    ...                Literal examples remain findings: ${example}, @{example}, &{example}, %{EXAMPLE}.
    ...                Escaped examples do not: \${example}, \@{example}, \&{example}, \%{EXAMPLE}.
    No Operation
