import ast

import pytest
from robot.api import get_model

from robocop.linter.utils.misc import find_escaped_variables, first_lineno, last_lineno

MODEL = """# comment before sections

*** Settings ***
Documentation    Suite doc.


*** Variables ***
${VAR}    value


*** Test Cases ***
Templated    argument
    ...    continuation

Test
    [Documentation]    Doc.
    FOR    ${item}    IN    a    b
        IF    $item == 'a'
            Log    ${item}
        ELSE IF    $item == 'b'
            Log    b
        ELSE
            WHILE    True
                BREAK
            END
        END
    END
    TRY
        Fail    message
    EXCEPT    message
        No Operation
    FINALLY
        Log    finally
    END
    # trailing comment


*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Log    ${arg}

*** Comments ***

"""


def test_first_and_last_lineno_match_robot_framework(tmp_path):
    source = tmp_path / "test.robot"
    source.write_text(MODEL, encoding="utf-8")
    model = get_model(source)

    for node in ast.walk(model):
        assert first_lineno(node) == node.lineno, node
        assert last_lineno(node) == node.end_lineno, node


@pytest.mark.parametrize(
    ("string", "expected"),
    [
        ("text", []),
        ("${var}", []),
        ("${var}[0]", []),
        ("$ {var}", []),
        ("\\${var}", []),
        ("$var", ["var"]),
        ("$ var", ["var"]),
        ("${var}_$other", ["other"]),
        ("$var_${other}", ["var_"]),
    ],
)
def test_find_escaped_variables(string, expected):
    assert find_escaped_variables(string) == expected
