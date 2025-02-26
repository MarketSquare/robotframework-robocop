.. _ReplaceWithVAR:

ReplaceWithVAR
================================

Replace ``Set Variable``, ``Create Dictionary``, ``Create List`` and ``Catenate`` keywords with ``VAR``.

.. |FORMATTERNAME| replace:: ReplaceWithVAR
.. include:: disabled_hint.txt

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                ${var}    Set Variable    value
                Set Suite Variable    ${SUITE_VAR}    ${var}
                ${list}    Create List    ${var}    second value
                ${string}    Catenate    join  with  spaces

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                VAR    ${var}    value
                VAR    ${SUITE_VAR}    ${var}    scope=SUITE
                VAR    @{list}    ${var}    second value
                VAR    ${string}    join    with    spaces    separator=${SPACE}

Variable scope
---------------

``VAR`` syntax supports setting the scope of the variable with ``scope=`` parameter. It's equivalent of the following
keywords:

 - Set Local Variable
 - Set Task Variable
 - Set Test Variable
 - Set Suite Variable
 - Set Global Variable

Other keywords such as ``Set Variable``, ``Catenate``, ``Create Dictionary`` and ``Create List`` create variable in the
local scope. Local scope is omitted by default but can be explicitly set by using ``explicit_local`` parameter.

``Set Suite Variable`` with ``children=True`` is ignored as it is not possible to have the same behaviour with ``VAR``.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                ${var}   Set Variable    value
                Set Local Variable    ${local_variable}    value
                Set Task Variable    ${task_variable}    value
                Set Test Variable    ${test_variable}
                Set Suite Variable    ${suite_variable}    value with ${value}
                Set Suite Variable    ${suite_variable}    value with ${value}    children=${True}  # ignored
                Set Global Variable   ${global_variable}    value

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                VAR    ${var}    value
                VAR    ${local_variable}    value
                VAR    ${task_variable}    value    scope=TASK
                VAR    ${test_variable}    ${test_variable}    scope=TEST
                VAR    ${suite_variable}    value with ${value}    scope=SUITE
                Set Suite Variable    ${suite_variable}    value with ${value}    children=${True}  # ignored
                VAR    ${global_variable}    value    scope=GLOBAL

    .. tab-item:: After (explicit_local = True)

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                VAR    ${var}    value    scope=LOCAL
                VAR    ${local_variable}    value    scope=LOCAL
                VAR    ${task_variable}    value    scope=TASK
                VAR    ${test_variable}    ${test_variable}    scope=TEST
                VAR    ${suite_variable}    value with ${value}    scope=SUITE
                Set Suite Variable    ${suite_variable}    value with ${value}    children=${True}  # ignored
                VAR    ${global_variable}    value    scope=GLOBAL

Catenate
--------

``Catenate`` keyword will be replaced with VAR. Separator is set using ``separator=`` parameter. ``Catenate`` keywords
can be ignored by setting ``replace_catenate`` parameter to ``False``.

Create Dictionary
------------------

``Create Dictionary`` keyword will be replaced with VAR. Variable name will change from ``${name}`` to ``&{name}``
to reflect the type of the variable. ``Create Dictionary`` keywords can be ignored by setting
``replace_create_dictionary`` parameter to ``False``.

Create List
------------

``Create List`` keyword will be replaced with VAR. Variable name will change from ``${name}`` to ``@{name}``
to reflect the type of the variable. ``Create List`` keywords can be ignored by setting
``replace_create_list`` parameter to ``False``.

Set Variable If
----------------

``Set Variable If`` keyword will be replaced with IF and VAR. If value in ELSE branch is not set, implicit
``${None}`` value will be used. Keywords with dynamic values (``@{values}``) are ignored since they may contain
``ELSE IF`` and ``ELSE`` branches that should be also converted. ``Set Variable If`` keywords can be ignored by setting
``replace_set_variable_if`` parameter to ``False``.


.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                ${var} =    Set Variable If    ${rc} > 0    whatever
                ${var}=    Set Variable If    ${rc} == 0    zero
                ...    ${rc} > 0    greater than zero    less then zero
                ${var}    Set Variable If    ${condition}    @{items}  # ignored

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Custom Keyword
                IF    ${rc} > 0
                    VAR    ${var}    whatever
                ELSE
                    VAR    ${var}    ${None}
                END
                IF    ${rc} == 0
                    VAR    ${var}    zero
                ELSE IF    ${rc} > 0
                    VAR    ${var}    greater than zero
                ELSE
                    VAR    ${var}    less then zero
                END
                ${var}    Set Variable If    ${condition}    @{items}  # ignored
