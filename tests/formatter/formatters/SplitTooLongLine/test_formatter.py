from tests.formatter import FormatterAcceptanceTest


class TestSplitTooLongLine(FormatterAcceptanceTest):
    FORMATTER_NAME = "SplitTooLongLine"

    def test_split_too_long_lines(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_arg=False"]
        self.compare(
            source="tests.robot",
            expected="feed_until_line_length.robot",
            configure=configure,
            space_count=4,
            test_on_version=">=5",
        )

    def test_split_too_long_lines_4(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_arg=False"]
        self.compare(
            source="tests.robot",
            expected="feed_until_line_length_4.robot",
            config=configure,
            test_on_version="==4",
        )

    def test_split_too_long_lines_split_on_every_arg(self):
        self.compare(
            source="tests.robot",
            expected="split_on_every_arg.robot",
            configure=[f"{self.FORMATTER_NAME}.line_length=80"],
            test_on_version=">=5",
        )

    def test_split_too_long_lines_split_on_every_arg_4(self):
        self.compare(
            source="tests.robot",
            expected="split_on_every_arg_4.robot",
            configure=[f"{self.FORMATTER_NAME}.line_length=80"],
            test_on_version="==5",
        )

    def test_split_lines_with_multiple_assignments(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_arg=False"]
        self.compare(
            source="multiple_assignments.robot",
            expected="multiple_assignments_until_line_length.robot",
            configure=configure,
        )

    def test_split_lines_with_multiple_assignments_on_every_arg(self):
        self.compare(
            source="multiple_assignments.robot",
            expected="multiple_assignments_on_every_arg.robot",
            configure=[f"{self.FORMATTER_NAME}.line_length=80"],
        )

    def test_split_lines_with_multiple_assignments_on_every_arg_120(self):
        self.compare(
            source="multiple_assignments.robot",
            expected="multiple_assignments_on_every_arg_120.robot",
        )

    def test_disablers(self):
        self.compare(
            source="disablers.robot",
            configure=[f"{self.FORMATTER_NAME}.line_length=80"],
            not_modified=True,
            test_on_version=">=5",
        )

    def test_continuation_indent(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_arg=False"]
        self.compare(
            source="continuation_indent.robot",
            expected="continuation_indent_feed.robot",
            configure=configure,
            space_count=2,
            continuation_indent=4,
            indent=2,
            test_on_version=">=5",
        )
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_arg=True"]
        self.compare(
            source="continuation_indent.robot",
            expected="continuation_indent_split.robot",
            configure=configure,
            space_count=2,
            continuation_indent=4,
            indent=2,
            test_on_version=">=5",
        )

    def test_variables_split(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_value=True"]
        self.compare(
            source="variables.robot",
            expected="variables_split_on_every_value.robot",
            configure=configure,
        )

    def test_variables_feed(self):
        configure = [f"{self.FORMATTER_NAME}.line_length=80", f"{self.FORMATTER_NAME}.split_on_every_value=False"]
        self.compare(
            source="variables.robot",
            expected="variables_feed.robot",
            configure=configure,
        )

    def test_skip_keywords(self):
        configure = [
            f"{self.FORMATTER_NAME}.line_length=80",
            f"{self.FORMATTER_NAME}.skip_keyword_call=thisisakeyword",
            rf"{self.FORMATTER_NAME}.skip_keyword_call_pattern=(i?)sets\sthe\svariable",
        ]
        self.compare(
            source="tests.robot",
            expected="skip_keywords.robot",
            configure=configure,
            test_on_version=">=5",
        )

    def test_comments(self):
        configure = [f"{self.FORMATTER_NAME}.split_on_every_value=False"]
        self.compare(
            source="comments.robot", configure=configure, select=[self.FORMATTER_NAME, "AlignVariablesSection"]
        )
        configure = [
            f"{self.FORMATTER_NAME}.split_on_every_value=False",
            f"{self.FORMATTER_NAME}.split_single_value=True",
        ]
        self.compare(
            source="comments.robot",
            expected="comments_split_scalar.robot",
            configure=configure,
            select=[self.FORMATTER_NAME, "AlignVariablesSection"],
        )

    def test_ignore_comments(self):
        self.compare(
            source="comments.robot",
            expected="comments_skip_comments.robot",
            configure=[f"{self.FORMATTER_NAME}.split_on_every_value=False"],
            select=[self.FORMATTER_NAME, "AlignVariablesSection"],
            skip=["comments"],
        )

    def test_split_settings(self):
        self.compare(
            source="settings.robot",
            expected="settings_on_every_arg.robot",
            configure=[f"{self.FORMATTER_NAME}.split_on_every_setting_arg=True"],
        )

    def test_split_settings_feed_until_line_length(self):
        self.compare(
            source="settings.robot",
            expected="settings_until_line_length.robot",
            configure=[f"{self.FORMATTER_NAME}.split_on_every_setting_arg=False"],
        )

    def test_split_settings_feed_until_line_length_skip_comments(self):
        configure = [
            f"{self.FORMATTER_NAME}.split_on_every_setting_arg=False",
            f"{self.FORMATTER_NAME}.skip_comments=True",
        ]
        self.compare(
            source="settings.robot",
            expected="settings_until_line_length_skip_comments.robot",
            configure=configure,
        )

    def test_skip_sections(self):
        configure = [f"{self.FORMATTER_NAME}.skip_sections=variables"]
        self.compare(source="variables.robot", configure=configure, not_modified=True)
        self.compare(source="comments.robot", configure=configure, not_modified=True)
        configure = [f"{self.FORMATTER_NAME}.skip_sections=settings,testcases,keywords"]
        self.compare(source="settings.robot", configure=configure, not_modified=True)
        configure = [f"{self.FORMATTER_NAME}.skip_sections=settings,testcases"]
        self.compare(source="settings.robot", expected="settings_skip_tests.robot", configure=configure)

    def test_skip_sections_global(self):
        self.compare(source="variables.robot", skip_sections=["variables"], not_modified=True)
        self.compare(source="comments.robot", skip_sections=["variables"], not_modified=True)
        self.compare(source="settings.robot", skip_sections=["settings", "testcases", "keywords"], not_modified=True)
        self.compare(
            source="settings.robot", expected="settings_skip_tests.robot", skip_sections=["settings", "testcases"]
        )

    def test_split_on_single_value(self):
        configure = [f"{self.FORMATTER_NAME}.split_single_value=True", f"{self.FORMATTER_NAME}.line_length=80"]
        self.compare(
            source="variables.robot",
            expected="variables_split_scalar.robot",
            configure=configure,
        )

    def test_align_new_lines_alone(self):
        configure = [
            f"{self.FORMATTER_NAME}.align_new_line=True",
            f"{self.FORMATTER_NAME}.split_on_every_arg=False",
            f"{self.FORMATTER_NAME}.split_on_every_setting_arg=False",
            f"{self.FORMATTER_NAME}.line_length=51",
        ]
        self.compare(
            source="align_new_line.robot",
            configure=configure,
        )

    def test_align_new_lines(self):
        configure = [
            f"{self.FORMATTER_NAME}.align_new_line=True",
            f"{self.FORMATTER_NAME}.split_on_every_arg=False",
            f"{self.FORMATTER_NAME}.split_on_every_setting_arg=False",
            f"{self.FORMATTER_NAME}.line_length=51",
            "NormalizeSeparators.align_new_line=True",
            "NormalizeTags.enabled=False",
            "OrderTags.enabled=False",
        ]
        self.compare(
            source="align_new_line.robot",
            expected="align_new_line_all.robot",
            configure=configure,
            run_all=True,
        )

    def test_var_syntax(self):
        self.compare(source="VAR_syntax.robot", test_on_version=">=7")
