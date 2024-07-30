mixed-task-test-settings reporting task settings in __init__.robot file (#1101)
-------------------------------------------------------------------------------

Fixes the issue where all task settings (such as ``Task Tags``) were reported as W0326 ``mixed-task-test-settings``
violation in files without Test or Task section.
