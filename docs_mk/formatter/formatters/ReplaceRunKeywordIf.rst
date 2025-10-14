.. _ReplaceRunKeywordIf:

ReplaceRunKeywordIf
===================

Replace ``Run Keyword If`` keyword calls with IF expressions.

.. |FORMATTERNAME| replace:: ReplaceRunKeywordIf
.. include:: enabled_hint.txt

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Run Keyword If  ${condition}
                ...  Keyword  ${arg}
                ...  ELSE IF  ${condition2}  Keyword2
                ...  ELSE  Keyword3

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                IF    ${condition}
                    Keyword    ${arg}
                ELSE IF    ${condition2}
                    Keyword2
                ELSE
                    Keyword3
                END

Any return value will be applied to every ELSE/ELSE IF branch.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                ${var}  Run Keyword If  ${condition}  Keyword  ELSE  Keyword2

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                IF    ${condition}
                    ${var}    Keyword
                ELSE
                    ${var}    Keyword2
                END

Run Keywords inside Run Keyword If will be split into separate keywords.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Run Keyword If  ${condition}  Run Keywords  Keyword  ${arg}  AND  Keyword2

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                IF    ${condition}
                    Keyword    ${arg}
                    Keyword2
                END

Run Keyword If that assigns values but does not provide default branch will receive ELSE branch with Set Variable:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                ${var}  Run Keyword If  ${condition}  Keyword

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                IF    ${condition}
                    ${var}    Keyword
                ELSE
                    ${var}    Set Variable    ${None}
                END
