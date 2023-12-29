Consider Robot Framework development version as final version in rule version matching
---------------------------------------------------------------------------------------

Robot Framework development version (for example 7.0rc1) is considered as final version (for example 7.0) in our
version matcher. Thanks to this change it is easier to test rules with not released version - it's not required
to define exact version specifier anymore (for example '==7.0rc1').

It's internal change but can have effect on your custom rules if you have rule version specifier using development
version::

    "XYZ": Rule(
        rule_id="XYZ",
        name="custom-rule",
        msg="custom-message",
        severity=RuleSeverity.WARNING,
        version=">=4.0alpha",  # it is not allowed anymore, use >=4.0 instead
        )
