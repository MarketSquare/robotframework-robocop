.. _ReplaceEmptyValues:

ReplaceEmptyValues
===================

Replace empty values with ``${EMPTY}`` variable.

.. |FORMATTERNAME| replace:: ReplaceEmptyValues
.. include:: enabled_hint.txt


Empty variables, lists or elements in the list can be defined in a way that omits the value.
To be more explicit, this transformer replace such values with ``${EMPTY}`` variables:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            ${EMPTY_VALUE}
            @{EMPTY_LIST}
            &{EMPTY_DICT}
            @{LIST_WITH_EMPTY}
            ...    value
            ...
            ...    value3

    .. tab-item:: After

        .. code:: robotframework

            *** Variables ***
            ${EMPTY_VALUE}    ${EMPTY}
            @{EMPTY_LIST}     @{EMPTY}
            &{EMPTY_DICT}     &{EMPTY}
            @{LIST_WITH_EMPTY}
            ...    value
            ...    ${EMPTY}
            ...    value3

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`
