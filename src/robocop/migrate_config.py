from __future__ import annotations

import re
from typing import TYPE_CHECKING

import tomli_w

from robocop.files import load_toml_file

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

RENAMED_RULES = {
    "0201": "DOC01",
    "0202": "DOC02",
    "0203": "DOC03",
    "0204": "DOC04",
    "0601": "TAG01",
    "0602": "TAG02",
    "0603": "TAG03",
    "0605": "TAG05",
    "0606": "TAG06",
    "0607": "TAG07",
    "0608": "TAG08",
    "0609": "TAG09",
    "0610": "TAG10",
    "0611": "TAG11",
    "0701": "COM01",
    "0702": "COM02",
    "0703": "COM03",
    "0704": "COM04",
    "0705": "COM05",
    "0911": "IMP01",
    "0926": "IMP02",
    # "10101": "IMP03", # we had one rule id for two rules
    "10102": "IMP04",
    "1001": "SPC01",
    "1002": "SPC02",
    "1003": "SPC03",
    "1004": "SPC04",
    "1005": "SPC05",
    "1006": "SPC06",
    "1008": "SPC08",
    "1009": "SPC09",
    "1010": "SPC10",
    "1011": "SPC11",
    "1012": "SPC12",
    "1013": "SPC13",
    "1014": "SPC14",
    "variable-should-be-left-aligned": "variable-not-left-aligned",
    "1015": "SPC15",
    "1016": "SPC16",
    "suite-setting-should-be-left-aligned": "suite-setting-not-left-aligned",
    "1017": "SPC17",
    "1018": "SPC18",
    "0402": "SPC19",
    "0406": "SPC20",
    "0410": "SPC21",
    "0411": "SPC22",
    "0801": "DUP01",
    "0802": "DUP02",
    "0803": "DUP03",
    "0804": "DUP04",
    "0805": "DUP05",
    "0806": "DUP06",
    "0807": "DUP07",
    "0808": "DUP08",
    "0810": "DUP09",
    "0813": "DUP10",
    "0501": "LEN01",
    "0502": "LEN02",
    "0503": "LEN03",
    "0504": "LEN04",
    "0528": "LEN05",
    "0505": "LEN06",
    "0507": "LEN07",
    "0508": "LEN08",
    "0509": "LEN09",
    "0510": "LEN10",
    "0511": "LEN11",
    "0512": "LEN12",
    "0513": "LEN13",
    "0514": "LEN14",
    "0515": "LEN15",
    "0516": "LEN16",
    "0517": "LEN17",
    "0518": "LEN18",
    "0519": "LEN19",
    "0520": "LEN20",
    "0521": "LEN21",
    "0522": "LEN22",
    "0523": "LEN23",
    "0524": "LEN24",
    "0525": "LEN25",
    "0526": "LEN26",
    "0527": "LEN27",
    "0506": "LEN28",
    "0529": "LEN29",
    "0530": "LEN30",
    "0531": "LEN31",
    "0912": "VAR01",
    "0920": "VAR02",
    "0922": "VAR03",
    "0929": "VAR04",
    "0930": "VAR05",
    "0931": "VAR06",
    "0310": "VAR07",
    "0316": "VAR08",
    "0317": "VAR09",
    "0323": "VAR10",
    "0324": "VAR11",
    "0812": "VAR12",
    "0919": "ARG01",
    "0921": "ARG02",
    "0932": "ARG03",
    "0933": "ARG04",
    "0407": "ARG05",
    "0811": "ARG06",
    "0532": "ARG07",
    "0908": "DEPR01",
    "0319": "DEPR02",
    "0321": "DEPR03",
    "0322": "DEPR04",
    "0327": "DEPR05",
    "0328": "DEPR06",
    "0301": "NAME01",
    "0302": "NAME02",
    "0303": "NAME03",
    "0305": "NAME04",
    "0306": "NAME05",
    "0307": "NAME06",
    "0308": "NAME07",
    "0309": "NAME08",
    "0311": "NAME09",
    "0312": "NAME10",
    "0313": "NAME11",
    "0314": "NAME12",
    "0315": "NAME13",
    "0318": "NAME14",
    "0320": "NAME15",
    "0325": "NAME16",
    "0326": "NAME17",
    "0901": "MISC01",
    "0903": "MISC02",
    "0907": "MISC03",
    "0909": "MISC04",
    "0910": "MISC05",
    "0913": "MISC06",
    "0914": "MISC07",
    "0915": "MISC08",
    "0916": "MISC09",
    "0917": "MISC10",
    "0918": "MISC11",
    "0923": "MISC12",
    "0924": "MISC13",
    "0925": "MISC14",
    "10001": "KW01",
    "10002": "KW02",
    "10003": "KW03",
    "10101": "KW04",
    "0927": "ORD01",
    "0928": "ORD02",
}


def replace_severity_values(rule_name: str) -> str:
    if re.match("[IWE][0-9]{4,}", rule_name):
        for char in "IWE":
            rule_name = rule_name.replace(char, "")
    return rule_name


def convert_rule_list(rules: list[str]) -> list[str]:
    """
    Convert rule names and ids to new ones.

    Removes optional severity. Rule patterns (``name*``) are ignored.
    """
    no_sev = [replace_severity_values(rule) for rule in rules]
    return [RENAMED_RULES.get(rule, rule) for rule in no_sev]


def convert_robocop_configure(configure: list[str]) -> list[str]:
    configure = [replace_severity_values(config) for config in configure]
    new_configure = []
    for config in configure:
        try:
            name, param_and_value = config.split(":", maxsplit=1)
            name = RENAMED_RULES.get(name, name)
            param, value = param_and_value.split(":", maxsplit=1)
            new_configure.append(f"{name.strip()}.{param.strip()}={value.strip()}")
        except ValueError:
            continue
    return new_configure


def convert_robotidy_configure(configure: list[str]) -> list[str]:
    new_configure = []
    for config in configure:
        try:
            name, param_and_value = config.split(":", maxsplit=1)
            param, value = param_and_value.split("=", maxsplit=1)
            new_configure.append(f"{name.strip()}.{param.strip()}={value.strip()}")
        except ValueError:
            continue
    return new_configure


def convert_skips(old_config: dict) -> list[str]:
    old_skips = [
        "documentation",
        "return_values",
        "settings",
        "arguments",
        "setup",
        "teardown",
        "timeout",
        "template",
        "return",
        "tags",
        "comments",
        "block_comments",
    ]
    return [name for name in old_skips if old_config.get(f"skip_{name}", False)]


def convert_target_version(old_value: str) -> int | str:
    """Convert target_version from rf4 to 4."""
    try:
        return int(old_value.lower().replace("rf", ""))
    except ValueError:
        return old_value


def copy_keys(src_dict: dict, keys: dict[str, str | tuple[str, Callable]]) -> dict:
    """
    Copy values from one dict to another.

    Keys are in old_key: new_key format. new_key may be a tuple in (new_key, convert_fn) format.
    """
    dst_dict = {}
    for old_key, new_key in keys.items():
        if old_key in src_dict:
            if isinstance(new_key, tuple):
                dst_dict[new_key[0]] = new_key[1](src_dict[old_key])
            else:
                dst_dict[new_key] = src_dict[old_key]
    return dst_dict


def split_config_from_select(select: list[str], configure: list[str]) -> tuple[list[str], list[str]]:
    new_select = []
    for formatter in select:
        if ":" not in formatter:
            new_select.append(formatter)
        else:
            try:
                name, param_and_value = formatter.split(":", maxsplit=1)
                name = RENAMED_RULES.get(name, name)
                param, value = param_and_value.split("=", maxsplit=1)
                new_select.append(name)
                configure.append(f"{name.strip()}.{param.strip()}={value.strip()}")
            except ValueError:
                continue
    return new_select, configure


def migrate_deprecated_configs(config_path: Path) -> None:
    # TODO: Warn that file should have [tool.robocop] and [tool.robotidy] sections
    config = load_toml_file(config_path)
    tool_config = config.get("tool", {})
    if not tool_config:
        print("No [tool] section found.")
        return
    robotidy_config = tool_config.get("robotidy", {})
    robocop_config = tool_config.get("robocop", {})
    if not robotidy_config and not robocop_config:
        print("No [tool.robocop] or [tool.robotidy] section found.")
        return
    migrated = copy_keys(
        robocop_config,
        {
            "paths": "include",
            "ignore": "exclude",
            "ignore_default": "exclude_default",
            "language": "language",
            "verbose": "verbose",
            # "filetypes": "",
        },
    )
    migrated["lint"] = copy_keys(
        robocop_config,
        {
            "include": ("select", convert_rule_list),
            "exclude": ("ignore", convert_rule_list),
            "reports": "reports",
            "format": ("issue_format", lambda x: x.replace("{source_rel}", "{source}")),
            "threshold": "threshold",
            "persistent": "persistent",
            "ignore_git_dir": "ignore_git_dir",
            "ext_rules": "custom_rules",
            "rules": "custom_rules",
            "configure": ("configure", convert_robocop_configure),
        },
    )
    if "output" in robocop_config:
        if "reports" in migrated["lint"]:
            migrated["lint"]["reports"].append("text_file")
        else:
            migrated["lint"]["reports"] = ["text_file"]
        if "configure" in migrated["lint"]:
            migrated["lint"]["configure"].append(f"text_file.output_path={robocop_config['output']}")
        else:
            migrated["lint"]["configure"] = [f"text_file.output_path={robocop_config['output']}"]
    migrated["format"] = copy_keys(
        robotidy_config,  # load-transformers / --custom-transformers
        {
            "transform": "select",
            "check": "check",
            "diff": "diff",
            "overwrite": "overwrite",
            "load_transformers": "custom_formatters",
            "custom_transformers": "custom_formatters",
            "line_length": "line_length",
            "separator": "separator",
            "spacecount": "space_count",
            "continuation_indent": "continuation_indent",
            "lineseparator": "line_separator",
            "startline": "start_line",
            "endline": "end_line",
            "skip_sections": "skip_sections",
            "skip_keyword_call": "skip_keyword_call",
            "skip_keyword_call_pattern": "skip_keyword_call_pattern",
            "configure": ("configure", convert_robotidy_configure),
        },
    )
    if "select" in migrated["format"]:
        migrated["format"]["select"], migrated["format"]["configure"] = split_config_from_select(
            migrated["format"]["select"], migrated["format"].get("configure", [])
        )
    if skips := convert_skips(robotidy_config):
        migrated["format"]["skip"] = skips
    if "target_version" in robotidy_config:
        migrated["target_version"] = convert_target_version(robotidy_config["target_version"])
    if not migrated["lint"]:
        migrated.pop("lint")
    if not migrated["format"]:
        migrated.pop("format")
    if not migrated:
        print("Nothing to migrate.")
        return
    config["tool"]["robocop"] = migrated
    config["tool"].pop("robotidy", None)
    dest = config_path.parent / f"{config_path.stem}_migrated.toml"
    with open(dest, "wb") as fp:
        tomli_w.dump(config, fp)
