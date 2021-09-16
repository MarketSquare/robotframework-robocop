from robocop.checkers import get_rules_for_atest


def pytest_generate_tests(metafunc):
    if "rule" not in metafunc.fixturenames:
        return
    auto_discovered_rules = [rule for category, rule in get_rules_for_atest()]
    metafunc.parametrize("rule", auto_discovered_rules)
