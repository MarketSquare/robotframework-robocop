.. _ReplaceBreakContinue:

ReplaceBreakContinue
=====================

Replace ``Continue For Loop`` and ``Exit For Loop`` keyword variants with ``CONTINUE`` and ``BREAK`` statements.

.. note::
    Required Robot Framework version: >=5.0

.. |FORMATTERNAME| replace:: ReplaceBreakContinue
.. include:: enabled_hint.txt

It will replace ``Continue For Loop`` and ``Exit For Loop`` keywords with ``CONTINUE`` and ``BREAK`` respectively:


.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            Test
                WHILE    $flag
                    Continue For Loop
                END
                FOR    ${var}    IN    abc
                    Exit For Loop
                END

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Test
                WHILE    $flag
                    CONTINUE
                END
                FOR    ${var}    IN    abc
                    BREAK
                END

Conditional variants are also handled. Shorter IFs can be also formatted to inline ``IF`` with :ref:`InlineIf` transformer:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            Test
                WHILE    $flag
                    Continue For Loop If    $condition
                END
                FOR    ${var}    IN    abc
                    Exit For Loop If    $condition
                END

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Test
                WHILE    $flag
                    IF    $condition
                        CONTINUE
                    END
                END
                FOR    ${var}    IN    abc
                    IF    $condition
                        BREAK
                    END
                END

``Continue For Loop`` and ``Exit For Loop`` along with conditional variants outside of the loop are ignored.
