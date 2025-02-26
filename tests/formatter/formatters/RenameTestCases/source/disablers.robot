*** Test Cases ***
starting with small case  # robotidy: off
    log  1
# robotidy: off
Ending with dot.
    No Operation
# robotidy: on
Ending with dot and containing variables .    column name    another column  # robotidy: off
    No Operation

Containing replace pattern JIRA-1234
    [Tags]    tag
    No Operation

Remove special chars: ?$@
    No Operation
