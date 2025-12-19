*** Comments ***
This is a Comments section where free-form text is expected.
The following patterns should NOT be detected as commented-out code:
# Library    Collections
# ${var}=    Get Value
# [Tags]    smoke
# IF    ${condition}
Even without # prefix, code patterns should not trigger here.
Library    Collections
${var}=    Get Value
[Tags]    smoke
IF    ${condition}

*** Settings ***
Documentation    Test file for commented-out-code rule
# Library    SeleniumLibrary
# Resource    keywords.resource
# Variables    config.py
# Suite Setup    Open Browser    ${URL}    chrome
# Suite Teardown    Close All Browsers
# Test Setup    Reset State
# Metadata    Version    1.0

*** Variables ***
${VALID_VAR}    value
# ${COMMENTED_VAR}=    commented value
# @{COMMENTED_LIST}=    a    b    c
# &{COMMENTED_DICT}=    key=value

*** Test Cases ***
Test With Valid Comments
    [Documentation]    Normal comments should NOT be detected
    Log    Hello
    # This is a normal comment
    # Another normal comment without code patterns
    # Remember to update the documentation
    Log    World

Test With TODO Marker
    [Documentation]    Comments with TODO markers should be ignored even with code patterns
    Log    Hello
    # TODO: ${var}=    Get Value
    # FIXME: [Tags]    smoke
    # TODO: IF    ${condition}
    Log    World

*** Keywords ***
Keyword With Assignment Pattern
    [Documentation]    Variable assignment detection
    # ${var}=    Get Value
    # ${result}=  Keyword Call
    # @{list}=    Create List    1    2    3
    # &{dict}=    Create Dictionary    key=value
    Log    Done

Keyword With Setting Brackets
    [Documentation]    Setting bracket detection
    # [Tags]    smoke    regression
    # [Arguments]    ${arg1}    ${arg2}
    # [Documentation]    Commented out docs
    # [Setup]    Initialize
    # [Teardown]    Cleanup
    # [Template]    My Template
    # [Timeout]    5s
    # [Return]    ${value}
    Log    Done

Keyword With Control Structures
    [Documentation]    Control structure detection (uppercase only)
    # IF    ${condition}
    # ELSE IF    ${other}
    # ELSE
    # END
    # FOR    ${item}    IN    @{items}
    # WHILE    ${condition}
    # TRY
    # EXCEPT
    # FINALLY
    # BREAK
    # CONTINUE
    # RETURN
    # GROUP    name
    Log    Done

Keyword With Lowercase Control Words
    [Documentation]    Lowercase control words should NOT be detected (they are prose)
    # If you need help, ask
    # For more information see docs
    # While this works, consider alternatives
    # Try to avoid this pattern
    # Break the loop manually
    # Continue reading for more details
    # Return to the main menu
    # Group these items together
    # End of section
    # Else you can use option B
    Log    Done

Keyword With Mixed Comments
    [Documentation]    Mixed valid and invalid comments
    # Normal comment without code
    Log    Action
    # ${result}=    Some Keyword
    # TODO: remember to check this
    Log    Done

Keyword With Inline Comment
    Log    Hello  # ${var}=    inline assignment
    Log    World  # normal inline comment
    Log    Test   # IF    ${x}

Keyword With Long Comment
    # ${VERY_LONG_VARIABLE_NAME}=    This is a very long value that exceeds forty chars
    Log    Done

Keyword With Code Examples In Documentation
    [Documentation]    This keyword shows how to use various features.
    ...    Example usage:
    ...    # ${result}=    Get Value
    ...    # [Tags]    smoke
    ...    # IF    ${condition}
    ...    These comments should NOT trigger the rule.
    Log    Documentation examples are ignored

Keyword With Multiple Hashes
    [Documentation]    Block comments with patterns inside
    ### ${var}=    Get Value
    ## [Tags]    smoke
    ### IF    ${condition}
    Log    Done

Keyword With Non Setting Brackets
    [Documentation]    Invalid setting names should NOT trigger via setting pattern
    # [not a setting]
    # [Random] value
    # [Foo]    bar
    Log    Done

Keyword With Prose And Variables
    [Documentation]    Prose with variables should NOT trigger (no assignment)
    # Use ${var} for this
    # The ${USER} variable should be set
    # Check if ${result} is correct
    Log    Done

Keyword With Empty And Minimal Comments
    [Documentation]    Edge cases with minimal content
    #
    #
    Log    Done

Keyword With Separator But No Assignment
    [Documentation]    These have separators but no assignment/setting/control - NOT detected
    # Log    Hello World
    # Should Be Equal    a    b
    # Sleep    5s
    Log    Done

Keyword With Settings Section Statements
    [Documentation]    Settings section statements like Library, Resource, Variables
    # Library    Collections
    # Library    String
    # Resource    common.resource
    # Resource    ../resources/utils.resource
    # Variables    vars.py
    # Suite Setup    Initialize
    # Suite Teardown    Cleanup
    # Test Setup    Prepare Test
    # Test Teardown    Finish Test
    # Metadata    Author    John
    # Force Tags    smoke
    # Default Tags    regression
    Log    Done

Keyword With Lowercase Settings Words
    [Documentation]    Lowercase settings words should NOT be detected (they are prose)
    # Library is a useful feature
    # Resource allocation is important
    # Variables can be tricky
    # The suite setup was successful
    # After test teardown, check results
    # Check the metadata for details
    Log    Done

Keyword With Complete FOR Loop Block
    [Documentation]    Complete FOR loop block commented out
    # FOR    ${item}    IN RANGE    10
    #     Log    ${item}
    #     ${result}=    Process Item    ${item}
    # END
    Log    Done

Keyword With Complete IF Block
    [Documentation]    Complete IF/ELSE block commented out
    # IF    ${condition}
    #     Log    Condition is true
    #     ${value}=    Get True Value
    # ELSE
    #     Log    Condition is false
    #     ${value}=    Get False Value
    # END
    Log    Done

Keyword With TRY EXCEPT Block
    [Documentation]    Complete TRY/EXCEPT block commented out
    # TRY
    #     ${result}=    Risky Operation
    # EXCEPT    Error message
    #     Log    Error occurred
    # FINALLY
    #     Cleanup Resources
    # END
    Log    Done

Keyword With VAR Syntax
    [Documentation]    RF 7.0+ VAR syntax
    # VAR    ${local}    value
    # VAR    @{list}    a    b    c
    # VAR    &{dict}    key=value
    # VAR    ${global}    value    scope=GLOBAL
    Log    Done

Keyword With RETURN Statement
    [Documentation]    RETURN with and without values
    # RETURN
    # RETURN    ${value}
    # RETURN    ${a}    ${b}    ${c}
    Log    Done

Keyword With Nested Control Structures
    [Documentation]    Nested IF inside FOR
    # FOR    ${item}    IN    @{items}
    #     IF    ${item} > 0
    #         Log    Positive
    #     ELSE
    #         Log    Non-positive
    #     END
    # END
    Log    Done

Keyword With WHILE Loop
    [Documentation]    Complete WHILE loop block
    # WHILE    ${counter} < 10
    #     ${counter}=    Evaluate    ${counter} + 1
    #     BREAK
    # END
    Log    Done

Keyword With GROUP Block
    [Documentation]    GROUP block for organizing code
    # GROUP    Setup Phase
    #     Initialize System
    #     Configure Settings
    # END
    Log    Done
