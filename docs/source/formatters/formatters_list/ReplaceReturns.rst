.. _ReplaceReturns:

ReplaceReturns
==============

Replace return statements (such as ``[Return]`` setting or ``Return From Keyword`` keyword) with new ``RETURN`` statement.

.. note::
    Required Robot Framework version: >=5.0

.. |FORMATTERNAME| replace:: ReplaceReturns
.. include:: enabled_hint.txt

This transformer replace ``[Return]`` statement with ``RETURN``:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Sub Keyword
                [Return]    ${value}

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Sub Keyword
                RETURN    ${value}

It also does replace ``Return From Keyword`` and ``Return From Keyword If``:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Return From Keyword If    $condition    ${value}
                Sub Keyword
                Return From Keyword    ${other_value}

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                IF    $condition
                    RETURN    ${value}
                END
                Sub Keyword
                RETURN    ${other_value}
