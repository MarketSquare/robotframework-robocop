import re
import sys
from pathlib import Path

import mkdocs_gen_files
from jinja2 import Template

sys.path.append(str(Path(__file__).parent.parent))
import robocop
from docs.rules_metadata import GROUPS_LOOKUP
from robocop.linter.rules import SeverityThreshold

RULES_LIST_TEMPLATE = """
# Rules list

This is the complete list of all Robocop rules grouped by categories.
If you want to learn more about the rules and their features, see [rules](linter/rules.md).

There are over {{ rules_length_in_10 }} rules available in Robocop and they are organized into the following categories:
{% for group in builtin_checkers %}
* {{ group.group_id }}: [{{ group.group_name }}](#{{ group.group_name | lower | replace(' ', '-') }})
{%- endfor %}

Below is the list of all Robocop rules.

{% for group in builtin_checkers %}
## {{ group.group_name }}

{{ group.group_docs }}
{% for rule_doc in group.rules %}

### {{ rule_doc.id }}: {{ rule_doc.name }}

{% if rule_doc.deprecated %}
> **Warning**
>
> Rule is deprecated.
{% endif %}

Added: `v{{ rule_doc.robocop_version }}`

Supported RF version `{{ rule_doc.version }}`

**Message**:

`{{ rule_doc.msg }}`

{% if rule_doc.docs|length %}

**Documentation**:

{{ rule_doc.docs }}

{% endif %}

{%- if rule_doc.style_guide is not none %}
**Style guide**:
{% for ref in rule_doc.style_guide %}
- [{{ ref }}](https://docs.robotframework.org/docs/style_guide{{ ref }})
{% endfor %}
{%- endif %}

{%- if rule_doc.severity_threshold is not none %}

> **Note: Severity thresholds**
>
> This rule supports dynamic severity configurable using thresholds ([severity-threshold](linter/rules.md#severity-threshold)).
> Parameter `{{ rule_doc.severity_threshold.param_name }}` will be used to determine issue severity depending on the thresholds.
>
> When configuring thresholds remember to also set `{{ rule_doc.severity_threshold.param_name }}` - its value should be lower or
> equal to the lowest value in the threshold.

{% endif %}

**Parameters**:

{% for rule_param in rule_doc.params %}
??? example "{{ rule_param.name }}"

    {{ rule_param.desc | capitalize }}

    **Default value:** {{ rule_param.default }}

    **Type:** {{ rule_param.type }}

    === ":octicons-command-palette-24: cli"

        ``` bash
        robocop check --configure {{ rule_doc.name }}.{{ rule_param.name }}={{ rule_param.default }}
        ```

    === ":material-file-cog-outline: toml"

        ``` toml
        [tool.robocop.lint]
        configure = [
            "{{ rule_doc.name }}.{{ rule_param.name }}={{ rule_param.default }}"
        ]
        ```
{% endfor %}

{% if not loop.last %}
---
{% endif %}

{% endfor %}


{% endfor %}
"""  # noqa: E501


def get_checker_docs() -> tuple[list[tuple], int]:
    """Load rules for dynamic docs generation"""
    doc_importer = robocop.linter.rules.DocumentationImporter()
    rules_count = 0
    for _, rule in doc_importer.get_builtin_rules():
        rules_count += 1
        severity_threshold = rule.config.get("severity_threshold", None)
        robocop_version = rule.added_in_version if rule.added_in_version else "\\-"
        match = re.match("(?P<group>.+)(?P<rule_no>[0-9]{2,})", rule.rule_id)
        group_id = match.group("group")
        try:
            group = GROUPS_LOOKUP[group_id]
        except KeyError:
            raise ValueError(f"Missing group metadata in rules_metadata.py for {group_id}.") from None
        group.rules.append(
            {
                "name": rule.name,
                "id": rule.rule_id,
                "severity": rule.severity.value,
                "desc": rule.description,
                "version": rule.supported_version,
                "robocop_version": robocop_version,
                "msg": rule.message,
                "docs": rule.docs,
                "deprecated": rule.deprecated,
                "params": [
                    {
                        "name": param.name,
                        "default": param.raw_value,
                        "type": param.param_type,
                        "desc": param.desc,
                    }
                    for param in rule.config.values()
                    if not isinstance(param, SeverityThreshold)
                ],
                "severity_threshold": severity_threshold,
                "style_guide": rule.style_guide_ref,
            }
        )
    sorted_groups = []
    for group in GROUPS_LOOKUP.values():
        group.rules = sorted(group.rules, key=lambda x: x["id"])
        sorted_groups.append(group)
    return sorted_groups, rules_count


def generate_rules_list():
    template = Template(RULES_LIST_TEMPLATE)

    rule_metadata, rules_count = get_checker_docs()
    rules_length_in_10 = (rules_count // 10) * 10
    context = {"builtin_checkers": rule_metadata, "rules_length_in_10": rules_length_in_10}
    return template.render(**context)


rules_list = generate_rules_list()

with mkdocs_gen_files.open("rules_list.md", "w") as f:
    f.write(rules_list)
