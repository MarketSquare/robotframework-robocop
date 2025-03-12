*** Test Cases ***
starting with small case  # robocop: fmt: off
    log  1
# robocop: fmt: off
Ending with dot.
    No Operation
# robocop: fmt: on
Ending with dot and containing variables .    column name    another column  # robocop: fmt: off
    No Operation

Containing replace pattern JIRA-1234
    [Tags]    tag
    No Operation

Remove special chars: ?$@
    No Operation
