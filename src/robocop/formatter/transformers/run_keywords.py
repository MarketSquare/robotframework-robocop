from robotidy.utils.misc import normalize_name


class RunKeywordVariant:
    def __init__(self, libname, name, resolve=1, branches=None, split_on_and=False):
        self.libname = normalize_name(libname)
        self.name = normalize_name(name)
        self.resolve = resolve
        self.branches = branches
        self.split_on_and = split_on_and


_RUN_KW = [
    RunKeywordVariant("BuiltIn", "Run Keyword"),
    RunKeywordVariant("BuiltIn", "Run Keyword And Continue On Failure"),
    RunKeywordVariant("BuiltIn", "Run Keyword And Expect Error", resolve=2),
    RunKeywordVariant("BuiltIn", "Run Keyword And Ignore Error"),
    RunKeywordVariant("BuiltIn", "Run Keyword And Return"),
    RunKeywordVariant("BuiltIn", "Run Keyword And Return If", resolve=2),
    RunKeywordVariant("BuiltIn", "Run Keyword And Return Status"),
    RunKeywordVariant("BuiltIn", "Run Keyword And Warn On Failure"),
    RunKeywordVariant("BuiltIn", "Run Keyword If", resolve=2, branches=["ELSE IF", "ELSE"]),
    RunKeywordVariant("BuiltIn", "Run Keyword If All Tests Passed"),
    RunKeywordVariant("BuiltIn", "Run Keyword If Any Tests Failed"),
    RunKeywordVariant("BuiltIn", "Run Keyword If Test Failed"),
    RunKeywordVariant("BuiltIn", "Run Keyword If Test Passed"),
    RunKeywordVariant("BuiltIn", "Run Keyword If Timeout Occurred"),
    RunKeywordVariant("BuiltIn", "Run Keyword Unless", resolve=2),
    RunKeywordVariant("BuiltIn", "Run Keywords", split_on_and=True),
    RunKeywordVariant("BuiltIn", "Repeat Keyword", resolve=2),
    RunKeywordVariant("BuiltIn", "Wait Until Keyword Succeeds", resolve=3),
]


def get_run_keywords():
    run_keywords = dict()
    for run_kw in _RUN_KW:
        run_keywords[run_kw.name] = run_kw
        run_keywords[f"{run_kw.libname}.{run_kw.name}"] = run_kw
    return run_keywords
