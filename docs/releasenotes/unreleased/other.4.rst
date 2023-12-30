Rule version matching allows for multiple Robot Framework versions (#1026)
--------------------------------------------------------------------------

When defining a rule it was possible to define Robot Framework version for which rule was enabled. Is is now also
possible to define range of versions using ``;`` as separator::

    rules = {
        "1105": Rule(
            rule_id="1105",
            name="range-5-and-6",
            msg="Rule that is only enabled for RF version higher than 5 and lower or equal to 6",
            severity=RuleSeverity.INFO,
            version=">5;<=6",
        ),
    }
