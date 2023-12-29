Rules can be now deprecated (#1025)
------------------------------------

Some of our rules were deprecated and then removed in the past. It could lead to issues when jumping from older
Robocop versions. Because of that we have introduced mechanism to deprecate the rules. It can be also used
in custom rules::

    rules = {
        "1102": Rule(rule_id="1102", name="custom-rule", msg="Example rule", deprecated=True, severity=RuleSeverity.ERROR),
    }

Deprecated rule implementation can be removed and only rule definition can stay. If the rule is used in ``--include``,
``--exclude`` or ``--configure`` warning will be printed::

    Rule W1102 deprecated is deprecated. Remove it from your configuration.

Deprecated rules can be now listed with ``DEPRECATED`` filter::

    robocop --list DEPRECATED
