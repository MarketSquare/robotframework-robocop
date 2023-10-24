Global variables used in the loop before assigning variable (#868)
------------------------------------------------------------------

The variable rules (such as W0919 ``unused-argument`` or I0920 ``unused-variable``) were not aware of the recursive
nature of the loops. For example if variable was used before it was declared in the loop (original value could
originate from global variable), it was marked as unused. Following code should not report unused variables anymore::

    Loop With Global Count
        FOR    ${item}    IN    @{LIST}
            Set To Dictionary    ${item}    displayOrder=${count}
            ${count}    Evaluate    ${count} + 1
        END
