{% for n in range(5) %}
*** Comments ***

{% for n in range(50) %}
Multiple comments here.
{% endfor %}
{% endfor %}
*** Settings ***
Resource     library.py
Library      Collections    WITH NAME  Collections
Library      Collections    AS  Collections
Library      other_library.py    WITH NAME  PrettyName
Library      WITH NAME
Library      Collections    WITH NAME    Coll ections
Library      Collections    AS    Coll ections

Documentation   doc
library         Library
resource        resource.robot
variablES       variables.py
suite setup     Keyword
suite Teardown  Keyword
test seTup      Keyword
Test teardown   Keyword
test tags      tag
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2
...             tag2    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3    tag3
...             tag2
default tags    defaulttag

*** Test Cases ***
{% for n in range(50) %}
Test{{ n }}
    [Setup]    Keyword
    [Documentation]    doc
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    [Tags]    tagname    tagname2    tagname3    tagname4    tagname5    tagname6    tagname7    tagname8    tagname9    tagname10
    ...    tagname11
    ${assign}=  Keyword Call
    Keyword Call
    ${assign1}    ${assign2}    Keyword Call
    IF    ${assign}    Inline If
    IF    True
        IF    True
            IF    True
                IF    True
                    IF    True
                        IF    True
                        IF    True
                        IF    True
                        IF    True
                            No Operation
                        END
                        END
                        END
                        END
                    END
                END
            ELSE IF    False
                No Operation
            ELSE
                No Operation
            END
        END
    END
    FOR    ${var}    IN    @{list}
        FOR    ${var2}    IN    @{list}
            FOR    ${var3}    IN    @{list}
                FOR    ${var4}    IN    @{list}
                    FOR    ${var5}    IN RANGE  1
                            Log    ${var}
                        WHILE    ${condition}
                            No Operation
                        END
                    END
                END
            END
        END
    END
    {% for n in range(50) %}
    Call Method With Some Parameters    ${arg1}    ${arg2}    ${long_argument_name3}    name=${value}    long_name=${long_value}
    ...    multi_value=${multi_value1}    multi_value=${multi_value2}    multi_value=${multi_value3}
    {% endfor %}
    [Teardown]    Keyword
{% endfor %}
{% for n in range(50) %}
Templated Test {{ n }}
    [Template]    Test Template
    arg1    arg2
    arg3    arg4
    arg5    arg6
{% endfor %}
*** Keywords ***
{% for n in range(50) %}
Keyword{{ n }}
    [Documentation]    doc
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    ...    multi
    [Tags]    tagname    tagname2    tagname3    tagname4    tagname5    tagname6    tagname7    tagname8    tagname9    tagname10
    ...    tagname11
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}    ${arg7}    ${arg8}    ${arg9}    ${arg10}=default
    ...    ${multi_argument}=
    ${assign}=  Keyword Call
    Keyword Call
    ${assign1}    ${assign2}    Keyword Call
    IF    ${assign}    Inline If
    IF    True
        IF    True
            IF    True
                IF    True
                    IF    True
                        IF    True
                        IF    True
                        IF    True
                        IF    True
                            No Operation
                        END
                        END
                        END
                        END
                    END
                END
            ELSE IF    False
                No Operation
            ELSE
                No Operation
            END
        END
    END
    FOR    ${var}    IN    @{list}
        FOR    ${var2}    IN    @{list}
            FOR    ${var3}    IN    @{list}
                FOR    ${var4}    IN    @{list}
                    FOR    ${var5}    IN RANGE  1
                            Log    ${var}
                        WHILE    ${condition}
                            No Operation
                        END
                    END
                END
            END
        END
    END
    {% for n in range(50) %}
    Call Method With Some Parameters    ${arg1}    ${arg2}    ${long_argument_name3}    name=${value}    long_name=${long_value}
    ...    multi_value=${multi_value1}    multi_value=${multi_value2}    multi_value=${multi_value3}
    VAR    ${variable}    value
    VAR    @{list_variable}    value    other_value    scope=SUITE
    TRY
        Do Dangerous Thing
    EXCEPT
        Ignore Error
    END
    {% endfor %}
    [Teardown]    Keyword
{% endfor %}
