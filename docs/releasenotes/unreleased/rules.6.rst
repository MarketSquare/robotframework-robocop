New rule replace-create-with-var (#973)
---------------------------------------

Added new I0328 ``replace-create-with-var`` rule.

Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the VAR
syntax. The VAR syntax is recommended over previously existing keywords. Starting from RF 7.0 Robocop will report
new issue when ``Create Dictionary`` or ``Create List`` keyword is used.

Example with Create keywords::

    *** Keywords ***
    Create Variables
        @{list}    Create List    a  b
        &{dict}    Create Dictionary    key=value

Can be now rewritten to::

    *** Keywords ***
    Create Variables
        VAR    @{list}    a  b
        VAR    &{dict}    key=value
