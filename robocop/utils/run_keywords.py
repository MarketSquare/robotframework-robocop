from robocop.utils.misc import normalize_robot_name


class RunKeywordVariant:
    def __init__(self, name, resolve=1, branches=None, split_on_and=False):
        self.name = normalize_robot_name(name)
        self.resolve = resolve
        self.branches = branches
        self.split_on_and = split_on_and


class RunKeywords(dict):
    def __init__(self, keywords):
        normalized_keywords = {}
        for keyword_variant in keywords:
            normalized_name = normalize_robot_name(keyword_variant.name)
            name_with_lib = f"builtin.{normalized_name}"
            normalized_keywords[normalized_name] = keyword_variant
            normalized_keywords[name_with_lib] = keyword_variant
        super().__init__(normalized_keywords)

    def __setitem__(self, keyword_name, kw_variant):
        normalized_name = normalize_robot_name(keyword_name)
        name_with_lib = f"builtin.{normalized_name}"
        super().__setitem__(normalized_name, kw_variant)
        super().__setitem__(name_with_lib, kw_variant)

    def __getitem__(self, keyword_name):
        normalized_name = normalize_robot_name(keyword_name)
        return super().__getitem__(normalized_name)

    def __missing__(self, keyword_name):
        return None


RUN_KEYWORDS = RunKeywords(
    [
        RunKeywordVariant("Run Keyword"),
        RunKeywordVariant("Run Keyword And Continue On Failure"),
        RunKeywordVariant("Run Keyword And Expect Error", resolve=2),
        RunKeywordVariant("Run Keyword And Ignore Error"),
        RunKeywordVariant("Run Keyword And Return"),
        RunKeywordVariant("Run Keyword And Return If", resolve=2),
        RunKeywordVariant("Run Keyword And Return Status"),
        RunKeywordVariant("Run Keyword And Warn On Failure"),
        RunKeywordVariant("Run Keyword If", resolve=2, branches=["ELSE IF", "ELSE"]),
        RunKeywordVariant("Run Keyword If All Tests Passed"),
        RunKeywordVariant("Run Keyword If Any Tests Failed"),
        RunKeywordVariant("Run Keyword If Test Failed"),
        RunKeywordVariant("Run Keyword If Test Passed"),
        RunKeywordVariant("Run Keyword If Timeout Occurred"),
        RunKeywordVariant("Run Keyword Unless", resolve=2),
        RunKeywordVariant("Run Keywords", split_on_and=True),
        RunKeywordVariant("Repeat Keyword", resolve=2),
        RunKeywordVariant("Wait Until Keyword Succeeds", resolve=3),
    ]
)


def skip_leading_tokens(tokens, break_token):
    for index, token in enumerate(tokens):
        if token.type == break_token:
            return tokens[index:]


def is_token_value_in_tokens(value, tokens):
    return any(value == token.value for token in tokens)


def split_on_token_value(tokens, value, resolve: int):
    """
    Split list of tokens into three lists based on token value.
    Returns tokens before found token, found token + `resolve` number of tokens, remaining tokens.
    """
    for index, token in enumerate(tokens):
        if value == token.value:
            prefix = tokens[:index]
            branch = tokens[index : index + resolve]
            remainder = tokens[index + resolve :]
            return prefix, branch, remainder
    else:
        return [], [], tokens


def iterate_keyword_names(keyword_node, name_token_type):
    tokens = skip_leading_tokens(keyword_node.data_tokens, name_token_type)
    yield from parse_run_keyword(tokens)


def parse_run_keyword(tokens):
    if not tokens:
        return
    yield tokens[0]
    run_keyword = RUN_KEYWORDS[tokens[0].value]
    if not run_keyword:
        return
    tokens = tokens[run_keyword.resolve :]
    if run_keyword.branches:
        if "ELSE IF" in run_keyword.branches:
            while is_token_value_in_tokens("ELSE IF", tokens):
                prefix, branch, tokens = split_on_token_value(tokens, "ELSE IF", 2)
                yield from parse_run_keyword(prefix)
        if "ELSE" in run_keyword.branches and is_token_value_in_tokens("ELSE", tokens):
            prefix, branch, tokens = split_on_token_value(tokens, "ELSE", 1)
            yield from parse_run_keyword(prefix)
            yield from parse_run_keyword(tokens)
            return
    elif run_keyword.split_on_and:
        yield from split_on_and(tokens)
        return
    yield from parse_run_keyword(tokens)


def split_on_and(tokens):
    if not is_token_value_in_tokens("AND", tokens):
        yield from (token for token in tokens)
        return
    while is_token_value_in_tokens("AND", tokens):
        prefix, branch, tokens = split_on_token_value(tokens, "AND", 1)
        yield from parse_run_keyword(prefix)
    yield from parse_run_keyword(tokens)
