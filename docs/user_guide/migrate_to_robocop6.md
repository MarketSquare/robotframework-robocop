# Migrating to Robocop 6

Robocop 6.0 is a major release of both ``Robocop`` and ``Robotidy`` tools. Nearly all core functionality has been
rewritten, refactored, or replaced. This causes several breaking changes and requires some changes in your
configuration.

The following document describes the most important changes and how to migrate your configuration. Use ``migrate``
command to migrate existing TOML configuration to the new format. Custom rules and argument files (now deprecated)
need to be migrated manually.

At first, adjust how you run Robocop using new ``check`` and ``format`` commands:

```bash
robocop check
robocop format
```

## ``migrate`` command

To migrate your configuration to the new version, use ``migrate`` command:

```bash
robocop migrate <config_path>
```

It will create a new file named ``<config_path>_migrated.toml`` with translated option names and their structure.
Rule ids are also converted to the new format, but patterns are not migrated (such as ``02*``).

Most of the configuration options are migrated automatically, but some of them require manual changes.

## Breaking changes in Robocop 6.0

### Command line options changes

Most of the options were renamed to normalise naming between two tools or to make it more user-friendly.
Some of the old options (like ``--exclude``) are now used for something else.

Rule selection options are now renamed:

- ``-i/--include`` became ``-s/--select``
- ``-e/--exclude`` became ``-i/--ignore``

---

File inclusion changes:

Previously, Robocop used ``paths`` argument and Robotidy ``src`` for selecting paths. It was then additionally
configured using options for filtering based on directory names or file types.

Now the role of ``paths`` was taken by ``include`` and ``--default--include`` (``*.robot`` and ``.resource``) options.
It is recommended to use cli for selecting a directory and leave it to robocop to find and filter out files.
If nothing is configured (we only run ``robocop check`` / ``robocop format``) then it will start from the current
directory. List of new or deprecated options:

- ``paths`` became ``--include``
- ``-ft/--filetypes`` is now deprecated in favour of using ``--include`` or ``--default-include`` option
- ``-g/--ignore`` became ``-e/--exclude`` (additionally excluded paths)
- ``-gd/--ignore-default`` became ``--default-exclude`` (paths excluded by default)

More on how to configure file paths in the [file discovery](../user_guide/intro.md#file-discovery) section in
the documentation.

---

``--list`` options were overhauled and became commands:

- Robocop ``--list`` used to list available rules became ``list rules`` command:

```bash
robocop list rules
```

- Robocop ``-lr/--list-reports`` used to list available reports became ``list reports command:

```bash
robocop list reports
```

- Robocop ``-lc / --list-configurables`` was overhauled and was incorporated to ``docs`` command:

```bash
robocop docs line-too-long
```

This command will print rule documentation and possible parameters.

- Robotidy ``--list`` used to list available formatters became ``list formatters`` command:

```bash
robocop list formatters
```

Describe options (``--desc``) are now replaced by ``docs`` command which can print rule, report or formatter
documentation.

---

Issue format ``--format`` is now renamed to ``--issue-format``. Please note that ``--issue-format`` is used only
for ``simple`` output format and ``extended`` output format is now used as a default.

---

Formatting options from Robotidy:

- ``--lineseparator`` became ``--line-ending``
- ``--spacecount`` became ``--space-count``
- ``-sl/--startline`` became ``--start-line``
- ``-el/--endline`` became ``--end-line``


``-rules / --ext-rules`` can be now only used under ``--custom-rules`` name.

``--load-transformers / --custom-transformers`` is now renamed to ``--custom-formatters``.

---

``-nr / --no-recursive`` is now deprecated. Similar behaviour can be reached by passing file paths to robocop or
configuring ``--exclude`` option.

### (Robotidy) Formatter deprecated --transform option

``--transform`` option used to select formatters is now deprecated. It has been replaced by ``--select`` which function
in a similar way but has one key difference: it does not support configuration. Configuration can be now passed only
to the dedicated ``--configure`` option.

Previous command:

```bash
robotidy --transform YourTransformer:parameter=value --configure DefaultTransformer:other_parameter=value
```

Can be now achieved by:

```bash
robocop format --select YourTransformer --configure YourTransformer.parameter=value --configure DefaultTransformer.other_parameter=value
```

All other ``transform`` mentions were also deprecated, for example:

- ``TRANSFORMERS`` list inside custom formatters to indicate order of the formatting should be now named ``FORMATTERS``
- ``Transformer`` class was renamed to ``Formatter``

### (Robocop) linter deprecated argument file

Linter alternative configuration file format - ``--argumentfile`` / ``.robocop`` file is now deprecated.
From now on we will only support one configuration file format (``toml`` based).

More information on the current configuration file syntax at [configuration](../configuration/index.md).

### Linter and formatter configuration syntax change

Robocop used two ``:`` to separate param and value in ``--config`` option. Robotidy used ``:`` and ``=``.
New Robocop now uses ``.`` and ``=``. Previous configuration changed from:

```bash
robocop --configure rule_or_report:param:value
robotidy --configure transformer:param=value
```

to:

```bash
robocop check --configure rule_or_report.param=value
robocop format --configure formatter.param=value
```

---

It is also no longer possible to chain multiple configurations in one ``configure`` call. The following example:

```bash
robotidy --configure formatter:param=value:param2=value
```

For readability reasons it can be now done only using separate options:

```bash
robocop format --configure formatter:param=value --configure formatter:param2=value
```

---

Passing configuration through file names that contain formatter is also deprecated:

```bash
robotidy --configure MyFormatter.py:param=2
```

Use the implicit name of the formatter instead:

```bash
robocop format --configure MyFormatter.param=2
```

### Configuration file syntax changes

Due to the merge of the tool, the syntax of the configuration file has changed. Most of the changes originate from the
changes to option names etc. Some changes are, however, dictated by the merge itself.

General settings are now available under ``tool.robocop`` section:

```toml
[tool.robocop]
exclude = ["excluded_dir/"]
```

Linter- or formatter-specific settings are available under ``lint`` or ``format`` sections:

```toml
[tool.robocop.lint]
configure = [
    "line-too-long.line_length=110"
]
[tool.robocop.format]
skip = ["documentation"]
configure = [
    "NormalizeSeparators.skip_documentation=False"
]
```

Documentation describes with examples where particular options should be configured.

### --target-version different input syntax

Formatter ``--target-version`` can now only accept numbers. Previous configuration such as ``--target-version RF5``
should be now ``--target-version 5``.

### Issue source is now relative by default

Relative path to source is now used by default when printing the linter issues.

Previous output, if run from ``robot_project`` directory:

```bash
D:/code/robot_project/tests/test.robot:19:59 [W] 0601 Tag '${var} space' should not contain spaces (tag-with-space)
```

New output:

```bash
robot_project/tests/test.robot:19:59 [W] 0601 Tag '${var} space' should not contain spaces (tag-with-space)
```

Previous issue format keyword ``source_rel`` is deprecated and ``source`` is used instead. It is still possible to use
absolute paths in output by configuring issue format to ``source_abs``:

```bash
robocop check --issue-format "{source_abs}:{line}:{col} [{severity}] {rule_id} {desc} ({name})"
```

### Replaced --output option with the text_file report

As part of the improved and safer design, linter option ``--output`` is now deprecated.

Instead, ``text_file`` report can be used:

```bash
robocop check --reports text_file --configure text_file.output_path=output/robocop.txt
```

``text_file`` report supports only ``simple`` issue output format.

### Deprecated singular global skip options in the formatter (Robotidy)

Robotidy offered multiple options to skip formatting of different statement types if the formatter allows it:

```text
--skip-documentation
--skip-return-values
--skip-keyword-call
--skip-keyword-call-pattern
--skip-settings
--skip-arguments
--skip-setup
--skip-teardown
--skip-timeout
--skip-template
--skip-return
--skip-tags
--skip-comments
--skip-block-comments
--skip-sections
```

Several options were combined under a single option named ``skip``:

```text
--skip documentation
--skip return-values
--skip settings
--skip arguments
--skip setup
--skip teardown
--skip timeout
--skip template
--skip return
--skip tags
--skip comments
--skip block-comments
--skip-sections
--skip-keyword-call
--skip-keyword-call-pattern
```

``skip`` accept multiple values from the cli or the configuration files.

Overriding skip on the formatter level still uses the previous syntax:

```bash
robocop format --configure AlignKeywordsSection.skip_arguments=True
```

### return_status report is now optional

Return status (exit code) of Robocop depended on internal, always enabled `return_status` report. It was calculated
based on parameter `quality_gate`. Default configuration:

```python
quality_gate = {
    'E': 0,
    'W': 0,
    'I': -1
}
```

It means that any error or warning will count towards exit code. Information messages by default were not counted
towards exit code. Actual exit code is the number of issues over the set limit, up to 255 (for example, with 'W': 100
and 105 warnings, exit code will be 5).

This behaviour wasn't clear to most and makes Robocop unpredictable when run in CI/CD pipelines. That's why we are
now making `return_status` report optional. It means that now exit code follows different logic:

- 0, if no rule violations were found
- 1, if violations were found
- 2, if Robocop terminated abnormally

It is possible to always return 0, ignoring any violations, with new ``--exit-zero`` flag. The previous behaviour
can be reproduced by simply enabling ``return_status`` report again:

```bash
robocop check --reports return_status
```

### compare_runs report is replaced with --compare

``compare_runs`` was special report that had to be enabled to compare reports results from current run with previous
runs. It was a bit of a workaround, that's why it was removed.

To compare results, use ``--compare`` flag:

```bash
robocop check --compare
```

Remember that you still need results from previous run (saved with ``--persistent``) and comparison is done on results
from the reports. Full example:

```bash
robocop check --persistent --compare --reports all
```

### Community rules are now simply 'non-default' rules

We have introduced non-default, 'community' rules in an effort to increase contributions from the community.
However, we noticed that it does not make sense to split our rules into 'internal' and 'community' ones.
Rules contributed from the users are often added as the default rules. For rules that should be optional, it is
enough to set them as non-default rules.

For that reason we are deprecating the term 'community' rules and all options related to it, such as filtering a list of
rules by community rules.

### Rule severity is now separate from the rule id

Robocop previously allowed selecting / ignoring / configuring rules using rule id with rule severity. For example:

```bash
robocop check --select W1010 --select 1011
```

Since rule severity is configurable, it could be potentially confusing. Additionally, it caused unindented issues when
using rule id with non-numeric characters (for example ``ERR001`` could be interpreted as ``RR001`` instead).
For those reasons it's not possible any more to refer to a rule using rule id with its severity. Use rule id without
severity or rule name instead:

```bash
robocop check --select DOC01 --select missing-doc-test-case
```

### Rules changes

We have reviewed all the rules to improve rule ids, names, documentation, messages, and overall design.
It would be too much to list of all the changes, but we will list all changes that have an impact on the users.

**Renamed messages**

Multiple rules messages were updated to avoid words such as ``should be`` or suggestions for fixes and to simply
state what's the actual issue. For example ``bad-block-indent`` message:

``Indent expected. Provide 2 or more spaces of indentation for statements inside block``

became:

``Not enough indentation inside block``

The goal was to have clear and shorter messages. The actual issue is well described thanks to the rule documentation
and new output format (which displays a source around the issue).

**Rule id changes**

Previous rule ids consisted of group id and unique rule number. For example ``0201`` - ``02`` was documentation group
id while ``01`` was unique rule number. This naming scheme wasn't clear and made it harder to categorise rule at first
glance. That's why we have switched to alphanumeric group names (for example ``DOC`` instead of ``02``).
Various groups are also additionally split into smaller subgroups. This change leads to backward incompatible
changes to all rule ids.

Documentation rules are now grouped under the 'DOC' group:

- ``0201`` became ``DOC01`` (``missing-doc-keyword``)
- ``0202`` became ``DOC02`` (``missing-doc-test-case``)
- ``0203`` became ``DOC03`` (``missing-doc-suite``)
- ``0204`` became ``DOC04`` (``missing-doc-resource-file``)

Tags rules are now grouped under the 'TAG' group:

- ``0601`` became ``TAG01`` (``tag-with-space``)
- ``0602`` became ``TAG02`` (``tag-with-or-and``)
- ``0603`` became ``TAG03`` (``tag-with-reserved-word``)
- ``0605`` became ``TAG05`` (``could-be-test-tags``)
- ``0606`` became ``TAG06`` (``tag-already-set-in-test-tags``)
- ``0607`` became ``TAG07`` (``unnecessary-default-tags``)
- ``0608`` became ``TAG08`` (``empty-tags``)
- ``0609`` became ``TAG09`` (``duplicated-tags``)
- ``0610`` became ``TAG10`` (``could-be-keyword-tags``)
- ``0611`` became ``TAG11`` (``tag-already-set-in-keyword-tags``)

Comments rules are now grouped under the 'COM' group:

- ``0701`` became ``COM01`` (``todo-in-comment``)
- ``0702`` became ``COM02`` (``missing-space-after-comment``)
- ``0703`` became ``COM03`` (``invalid-comment``)
- ``0704`` became ``COM04`` (``ignored-data``)
- ``0705`` became ``COM05`` (``bom-encoding-in-file``)

Import-related rules are now grouped under the 'IMP' group:

- ``0911`` became ``IMP01`` (``wrong-import-order``)
- ``0926`` became ``IMP02`` (``builtin-imports-not-sorted``)
- ``10101`` became ``IMP03`` (``non-builtin-imports-not-sorted``)
- ``10102`` became ``IMP04`` (``resources-imports-not-sorted``)

Spacing and whitespace-related rules are now grouped under the 'SPC' group:

- ``1001`` became ``SPC01`` (``trailing-whitespace``)
- ``1002`` became ``SPC02`` (``missing-trailing-blank-line``)
- ``1003`` became ``SPC03`` (``empty-lines-between-sections``)
- ``1004`` became ``SPC04`` (``empty-lines-between-test-cases``)
- ``1005`` became ``SPC05`` (``empty-lines-between-keywords``)
- ``1006`` became ``SPC06`` (``mixed-tabs-and-spaces``)
- ``1008`` became ``SPC08`` (``bad-indent``)
- ``1009`` became ``SPC09`` (``empty-line-after-section``)
- ``1010`` became ``SPC10`` (``too-many-trailing-blank-lines``)
- ``1011`` became ``SPC11`` (``misaligned-continuation``)
- ``1012`` became ``SPC12`` (``consecutive-empty-lines``)
- ``1013`` became ``SPC13`` (``empty-lines-in-statement``)
- ``1014`` became ``SPC14`` (``variable-should-be-left-aligned`` -> ``variable-not-left-aligned``)
- ``1015`` became ``SPC15`` (``misaligned-continuation-row``)
- ``1016`` became ``SPC16`` (``suite-setting-should-be-left-aligned`` -> ``suite-setting-not-left-aligned``)
- ``1017`` became ``SPC17`` (``bad-block-indent``)
- ``1018`` became ``SPC18`` (``first-argument-in-new-line``)
- ``0402`` became ``SPC19`` (``not-enough-whitespace-after-setting``)
- ``0406`` became ``SPC20`` (``not-enough-whitespace-after-newline-marker``)
- ``0410`` became ``SPC21`` (``not-enough-whitespace-after-variable``)
- ``0411`` became ``SPC22`` (``not-enough-whitespace-after-suite-setting``)

Duplications related rules are now grouped under the 'DUP' group:

- ``0801`` became ``DUP01`` (``duplicated-test-case"``)
- ``0802`` became ``DUP02`` (``duplicated-keyword``)
- ``0803`` became ``DUP03`` (``duplicated-variable``)
- ``0804`` became ``DUP04`` (``duplicated-resource``)
- ``0805`` became ``DUP05`` (``duplicated-library``)
- ``0806`` became ``DUP06`` (``duplicated-metadata``)
- ``0807`` became ``DUP07`` (``duplicated-variables-import``)
- ``0808`` became ``DUP08`` (``section-already-defined``)
- ``0810`` became ``DUP09`` (``both-tests-and-tasks``)
- ``0813`` became ``DUP10`` (``duplicated-setting``)

Length-related rules are now grouped under the 'LEN' group:

- ``0501`` became ``LEN01`` (``too-long-keyword``)
- ``0502`` became ``LEN02`` (``too-few-calls-in-keyword``)
- ``0503`` became ``LEN03`` (``too-many-calls-in-keyword``)
- ``0504`` became ``LEN04`` (``too-long-test-case``)
- ``0528`` became ``LEN05`` (``too-few-calls-in-test-case``)
- ``0505`` became ``LEN06`` (``too-many-calls-in-test-case``)
- ``0507`` became ``LEN07`` (``too-many-arguments``)
- ``0508`` became ``LEN08`` (``line-too-long``)
- ``0509`` became ``LEN09`` (``empty-section``)
- ``0510`` became ``LEN10`` (``number-of-returned-values``)
- ``0511`` became ``LEN11`` (``empty-metadata``)
- ``0512`` became ``LEN12`` (``empty-documentation``)
- ``0513`` became ``LEN13`` (``empty-force-tags``)
- ``0514`` became ``LEN14`` (``empty-default-tags``)
- ``0515`` became ``LEN15`` (``empty-variables-import``)
- ``0516`` became ``LEN16`` (``empty-resource-import``)
- ``0517`` became ``LEN17`` (``empty-library-import``)
- ``0518`` became ``LEN18`` (``empty-setup``)
- ``0519`` became ``LEN19`` (``empty-suite-setup``)
- ``0520`` became ``LEN20`` (``empty-test-setup``)
- ``0521`` became ``LEN21`` (``empty-teardown``)
- ``0522`` became ``LEN22`` (``empty-suite-teardown``)
- ``0523`` became ``LEN23`` (``empty-test-teardown``)
- ``0524`` became ``LEN24`` (``empty-timeout``)
- ``0525`` became ``LEN25`` (``empty-test-timeout``)
- ``0526`` became ``LEN26`` (``empty-arguments``)
- ``0527`` became ``LEN27`` (``too-many-test-cases``)
- ``0506`` became ``LEN28`` (``file-too-long``)
- ``0529`` became ``LEN29`` (``empty-test-template``)
- ``0530`` became ``LEN30`` (``empty-template``)
- ``0531`` became ``LEN31`` (``empty-keyword-tags``)

Variable-related rules are now grouped under the 'VAR' group:

- ``0912`` became ``VAR01`` (``empty-variable``)
- ``0920`` became ``VAR02`` (``unused-variable``)
- ``0922`` became ``VAR03`` (``variable-overwritten-before-usage``)
- ``0929`` became ``VAR04`` (``no-global-variable``)
- ``0930`` became ``VAR05`` (``no-suite-variable``)
- ``0931`` became ``VAR06`` (``no-test-variable``)
- ``0310`` became ``VAR07`` (``non-local-variables-should-be-uppercase``)
- ``0316`` became ``VAR08`` (``possible-variable-overwriting``)
- ``0317`` became ``VAR09`` (``hyphen-in-variable-name``)
- ``0323`` became ``VAR10`` (``inconsistent-variable-name``)
- ``0324`` became ``VAR11`` (``overwriting-reserved-variable``)
- ``0812`` became ``VAR12`` (``duplicated-assigned-var-name``)

Argument-related rules are now grouped under the 'ARG' group:

- ``0919`` became ``ARG01`` (``unused-argument``)
- ``0921`` became ``ARG02`` (``argument-overwritten-before-usage``)
- ``0932`` became ``ARG03`` (``undefined-argument-default``)
- ``0933`` became ``ARG04`` (``undefined-argument-value``)
- ``0407`` became ``ARG05`` (``invalid-argument``)
- ``0811`` became ``ARG06`` (``duplicated-argument-name``)
- ``0532`` became ``ARG07`` (``arguments-per-line``)

Deprecated syntax or code replacement recommendations are now grouped under the 'DEPR' group:

- ``0908`` became ``DEPR01`` (``if-can-be-used``)
- ``0319`` became ``DEPR02`` (``deprecated-statement``)
- ``0321`` became ``DEPR03`` (``deprecated-with-name``)
- ``0322`` became ``DEPR04`` (``deprecated-singular-header``)
- ``0327`` became ``DEPR05`` (``replace-set-variable-with-var``)
- ``0328`` became ``DEPR06`` (``replace-create-with-var``)

Naming rules are now grouped under the 'NAME' group:

- ``0301`` became ``NAME01`` (``not-allowed-char-in-name``)
- ``0302`` became ``NAME02`` (``wrong-case-in-keyword-name``)
- ``0303`` became ``NAME03`` (``keyword-name-is-reserved-word``)
- ``0305`` became ``NAME04`` (``underscore-in-keyword-name``)
- ``0306`` became ``NAME05`` (``setting-name-not-in-title-case``)
- ``0307`` became ``NAME06`` (``section-name-invalid``)
- ``0308`` became ``NAME07`` (``not-capitalized-test-case-title``)
- ``0309`` became ``NAME08`` (``section-variable-not-uppercase``)
- ``0311`` became ``NAME09`` (``else-not-upper-case``)
- ``0312`` became ``NAME10`` (``keyword-name-is-empty``)
- ``0313`` became ``NAME11`` (``test-case-name-is-empty``)
- ``0314`` became ``NAME12`` (``empty-library-alias``)
- ``0315`` became ``NAME13`` (``duplicated-library-alias``)
- ``0318`` became ``NAME14`` (``bdd-without-keyword-call``)
- ``0320`` became ``NAME15`` (``not-allowed-char-in-filename``)
- ``0325`` became ``NAME16`` (``invalid-section``)
- ``0326`` became ``NAME17`` (``mixed-task-test-settings``)

Other rules are now grouped under the 'MISC' group:

- ``0901`` became ``MISC01`` (``keyword-after-return``)
- ``0903`` became ``MISC02`` (``empty-return``)
- ``0907`` became ``MISC03`` (``nested-for-loop``)
- ``0909`` became ``MISC04`` (``inconsistent-assignment``)
- ``0910`` became ``MISC05`` (``inconsistent-assignment-in-variables``)
- ``0913`` became ``MISC06`` (``can-be-resource-file``)
- ``0914`` became ``MISC07`` (``if-can-be-merged``)
- ``0915`` became ``MISC08`` (``statement-outside-loop``)
- ``0916`` became ``MISC09`` (``inline-if-can-be-used``)
- ``0917`` became ``MISC10`` (``unreachable-code``)
- ``0918`` became ``MISC11`` (``multiline-inline-if``)
- ``0923`` became ``MISC12`` (``unnecessary-string-conversion``)
- ``0924`` became ``MISC13`` (``expression-can-be-simplified``)
- ``0925`` became ``MISC14`` (``misplaced-negative-condition``)

Miscellaneous keyword-related rules are now grouped under the 'KW' group:

- ``10001`` became ``KW01`` (``sleep-keyword-used``)
- ``10002`` became ``KW02`` (``not-allowed-keyword``)
- ``10003`` became ``KW03`` (``no-embedded-keyword-arguments``)
- ``10101`` became ``KW04`` (``unused-keyword``)

Order-related rules (except imports) are now grouped under the 'ORD' group:

- ``0927`` became ``ORD01`` (``test-case-section-out-of-order``)
- ``0928`` became ``ORD02`` (``keyword-section-out-of-order``)

### New syntax for custom rules

Previous rule design is deprecated in favour of a new, more OOP-like design.

Example of the old syntax:

```python
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

rules = {
    "1101": Rule(rule_id="1101", name="smth", msg="Keyword call after [Return] statement", severity=RuleSeverity.ERROR)
}


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after the [Return] statement."""

    reports = ("smth",)

    def visit_Keyword(self, node):  # noqa: N802
        (...)
        self.report("smth", node=node)
```

Rules are no longer defined in the global dictionaries. Each rule should be defined in their own class:

```python
from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker


class ExternalRule(Rule):
    """
    Keyword call after the ``[Return]`` statement.

    ``[Return]`` setting does not return from the keyword and only sets which variables will be returned.
    To avoid confusion, it is better to define it at the end of the keyword.
    """
    name = "smth"
    rule_id = "EXT01"
    message = "Keyword call after [Return] statement"
    severity = RuleSeverity.ERROR


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after the [Return] statement."""

    smth: ExternalRule

    def visit_Keyword(self, node):  # noqa: N802
        (...)
        self.report(self.smth, node=node)
```

Rules can be 'attached' to checkers that will be using them by using a class attribute together with a type hint:

```python
smth: ExternalRule
```

Robocop will find and instantiate such attributes.

Rule params should use now refer directly to such an attribute instead of previous
``self.param("rule_name", "param_name")`` calls:

```python
self.rule_name.param_name
```

Thanks to this design, it's also possible to move part of the implementation inside a rule class, with less
rule-specific code in the visitor.

Note that various import paths also changed. For example, from:

```python
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity
```

to:

```python
from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker
```

### New disabler syntax

We normalised Robocop and Robotidy disablers several releases ago, but the old syntax was still allowed. We are now
deprecating it for good. Due to merge and deprecation of Robotidy, we also deprecate ``robotidy`` directive.

Currently supported syntax for linter:

```python
# noqa
# robocop: off
# robocop: on
```

And formatter:

```python
# fmt: off
# fmt: on
# robocop: fmt: off
# robocop: fmt: on
```

Deprecated syntax:
```python
# robotidy: on
# robotidy: off
# robocop: enable
# robocop: disable
```

New syntax still supports disabling selected rules or formatters (``# robocop: off=rule_name``).

### Dropped support for Jinja templates in a rule message

Rule messages used Jinja templates:

```python
"Keyword argument '{{ name }}' is not used"
```

It was unnecessarily complex as we only used it for value substitution. There is no need to use any other Jinja
features. It is now replaced with Python format syntax:

```python
"Keyword argument '{name}' is not used"
```

It's important only for users who have custom rules using templates in messages.

### Dropped support for Robot Framework 3.2

Since Robocop supported Robot Framework >=3.2.2 and Robotidy >= 4.0, we had to use 4.0 as a baseline version.
Robocop can still be used to lint code written for RF 3, but you need an environment with at least RF 4 to run
Robocop.

### Dropped support for Python 3.8

Python 3.8 is no longer supported by Python foundation, and we are also dropping support for it.

### Normalised output path configuration in JSON and sarif reports

In this release we have added several new reports that are file-based (such as gitlab, sonarqube etc. reports).
To make it simpler and more logical, I have standardised how the output path can be configured for such reports.

The following configuration parameters are now deprecated in JSON and sarif reports:

- output_dir
- report_filename

Instead, we can use ``output_path`` to configure both directory and filename:

```bash
robocop check --reports sarif --configure sarif.output_path=reports/sarif.json
robocop check --reports gitlab --configure gitlab.output_path=reports/gitlab.json
```
