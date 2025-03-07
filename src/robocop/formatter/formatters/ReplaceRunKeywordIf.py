from robot.api.parsing import ElseHeader, ElseIfHeader, End, If, IfHeader, KeywordCall, Token

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc


def insert_separators(indent, tokens, separator):
    yield Token(Token.SEPARATOR, indent)
    for token in tokens[:-1]:
        yield token
        yield Token(Token.SEPARATOR, separator)
    yield tokens[-1]
    yield Token(Token.EOL)


class ReplaceRunKeywordIf(Formatter):
    """
    Replace ``Run Keyword If`` keyword calls with IF expressions.

    Following code:

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}
        ...  Keyword  ${arg}
        ...  ELSE IF  ${condition2}  Keyword2
        ...  ELSE  Keyword3
    ```

    Will be formatted to:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
        ELSE IF    ${condition2}
            Keyword2
        ELSE
            Keyword3
        END
    ```

    Any return value will be applied to every ``ELSE``/``ELSE IF`` branch:

    ```robotframework
    *** Keywords ***
    Keyword
        ${var}  Run Keyword If  ${condition}  Keyword  ELSE  Keyword2
    ```

    Output:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            ${var}    Keyword
        ELSE
            ${var}    Keyword2
        END
    ```

    Run Keywords inside Run Keyword If will be split into separate keywords:

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}  Run Keywords  Keyword  ${arg}  AND  Keyword2
    ```

    Output:

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
            Keyword2
        END
    ```
    """

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_KeywordCall(self, node):  # noqa: N802
        if not node.keyword:
            return node
        if misc.after_last_dot(misc.normalize_name(node.keyword)) == "runkeywordif":
            return self.create_branched(node)
        return node

    def create_branched(self, node):
        separator = node.tokens[0]
        assign = node.get_tokens(Token.ASSIGN)
        raw_args = node.get_tokens(Token.ARGUMENT)
        if len(raw_args) < 2:
            return node
        end = End([separator, Token(Token.END), Token(Token.EOL)])
        prev_if = None
        for branch in reversed(list(self.split_args_on_delimiters(raw_args, ("ELSE", "ELSE IF"), assign=assign))):
            if branch[0].value == "ELSE":
                if len(branch) < 2:
                    return node
                args = branch[1:]
                if self.check_for_useless_set_variable(args, assign):
                    continue
                header = ElseHeader([separator, Token(Token.ELSE), Token(Token.EOL)])
            elif branch[0].value == "ELSE IF":
                if len(branch) < 3:
                    return node
                header = ElseIfHeader(
                    [
                        separator,
                        Token(Token.ELSE_IF),
                        Token(Token.SEPARATOR, self.formatting_config.separator),
                        branch[1],
                        Token(Token.EOL),
                    ]
                )
                args = branch[2:]
            else:
                if len(branch) < 2:
                    return node
                header = IfHeader(
                    [
                        separator,
                        Token(Token.IF),
                        Token(Token.SEPARATOR, self.formatting_config.separator),
                        branch[0],
                        Token(Token.EOL),
                    ]
                )
                args = branch[1:]
            keywords = self.create_keywords(args, assign, separator.value + self.formatting_config.indent)
            if_block = If(header=header, body=keywords, orelse=prev_if)
            prev_if = if_block
        prev_if.end = end
        return prev_if

    def create_keywords(self, arg_tokens, assign, indent):
        keyword_name = misc.normalize_name(arg_tokens[0].value)
        if keyword_name == "runkeywords":
            return [
                self.args_to_keyword(keyword[1:], assign, indent)
                for keyword in self.split_args_on_delimiters(arg_tokens, ("AND",))
            ]
        if misc.is_var(keyword_name):
            keyword_token = Token(Token.KEYWORD_NAME, "Run Keyword")
            arg_tokens = [keyword_token, *arg_tokens]
        return [self.args_to_keyword(arg_tokens, assign, indent)]

    def args_to_keyword(self, arg_tokens, assign, indent):
        separated_tokens = list(
            insert_separators(
                indent,
                [*assign, Token(Token.KEYWORD, arg_tokens[0].value), *arg_tokens[1:]],
                self.formatting_config.separator,
            )
        )
        return KeywordCall.from_tokens(separated_tokens)

    @staticmethod
    def split_args_on_delimiters(args, delimiters, assign=None):
        split_points = [index for index, arg in enumerate(args) if arg.value in delimiters]
        prev_index = 0
        for split_point in split_points:
            yield args[prev_index:split_point]
            prev_index = split_point
        yield args[prev_index : len(args)]
        if assign and "ELSE" in delimiters and not any(arg.value == "ELSE" for arg in args):
            values = [Token(Token.ARGUMENT, "${None}")] * len(assign)
            yield [Token(Token.ELSE), Token(Token.ARGUMENT, "Set Variable"), *values]

    @staticmethod
    def check_for_useless_set_variable(tokens, assign):
        if not assign or misc.normalize_name(tokens[0].value) != "setvariable" or len(tokens[1:]) != len(assign):
            return False
        for var, var_assign in zip(tokens[1:], assign):
            if misc.normalize_name(var.value) != misc.normalize_name(var_assign.value):
                return False
        return True
