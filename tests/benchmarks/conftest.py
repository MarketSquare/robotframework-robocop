from robocop.checkers import get_rules


def pytest_generate_tests(metafunc):
    if "rule" not in metafunc.fixturenames:
        return
    auto_discovered_rules = [rule.name for category, rule in get_rules()]
    metafunc.parametrize("rule", auto_discovered_rules)
