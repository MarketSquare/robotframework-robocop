unused-variable when the variable is used in a Test Setup (#1062)
------------------------------------------------------------------

I0920 ``unused-variable`` was incorrectly reported if the variable was declared in the ``*** Variables ***`` section
and used in ``[Setup]``, ``[Teardown]`` or ``[Timeout]``.
