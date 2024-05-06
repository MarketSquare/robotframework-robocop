Task section not recognized for mixed-task-test-settings rule (#1074)
----------------------------------------------------------------------

If last section of the file wasn't Tasks section, Robocop assumed that file contains only Test Cases section. This
caused W0326 ``mixed-task-test-settings`` to be issued with incorrect message.

Thanks @MrBIN89 for finding the issue.
