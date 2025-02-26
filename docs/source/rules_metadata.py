from dataclasses import dataclass, field


@dataclass
class RulesGroup:
    """
    Class retaining metadata for group and its rules.
    """

    group_id: str
    group_name: str
    group_docs: str
    rules: list[dict] = field(default_factory=list)


GROUPS_LOOKUP = {
    "ARG": RulesGroup("ARG", "Arguments", "Rules for keyword arguments."),
    "COM": RulesGroup("COM", "Comments", "Rules for comments."),
    "DEPR": RulesGroup("DEPR", "Deprecated code", "Rules for deprecated code or code replacement recommendations."),
    "DOC": RulesGroup("DOC", "Documentation", "Rules for documentation."),
    "DUP": RulesGroup("DUP", "Duplications", "Rules for duplicated code such as settings or variables."),
    "ERR": RulesGroup("ERR", "Errors", "Rules for syntax errors and critical issues with the code."),
    "IMP": RulesGroup("IMP", "Imports", "Rules for resources, variables and libraries imports."),
    "KW": RulesGroup("KW", "Keywords", "Rules for keywords."),
    "LEN": RulesGroup("LEN", "Lengths", "Rules for lengths, such as length of the test case or the file."),
    "MISC": RulesGroup("MISC", "Miscellaneous", "Miscellaneous rules."),
    "NAME": RulesGroup("NAME", "Naming", "Naming rules."),
    "ORD": RulesGroup("ORD", "Order", "Ordering rules."),
    "SPC": RulesGroup("SPC", "Spacing", "Spacing and whitespace related rules."),
    "TAG": RulesGroup("TAG", "Tags", "Rules for  tags."),
    "VAR": RulesGroup("VAR", "Variables", "Rules for variables."),
}
