from pathlib import Path

from tests.formatter import FormatterAcceptanceTest


def get_relative_path(abs_path: Path) -> Path:
    cwd = Path.cwd()
    return abs_path.relative_to(cwd)


class TestGenerateDocumentation(FormatterAcceptanceTest):
    FORMATTER_NAME = "GenerateDocumentation"

    def test_formatter(self):
        self.compare(source="test.robot", test_on_version=">=5")

    def test_formatter_rf4(self):
        self.compare(source="test.robot", expected="test_rf4.robot", test_on_version="<=4")

    def test_formatter_overwrite(self):
        self.compare(
            source="test.robot",
            expected="overwrite.robot",
            configure=[f"{self.FORMATTER_NAME}.overwrite=True"],
            test_on_version=">=5",
        )

    def test_template_with_defaults(self):
        template_path = Path(__file__).parent / "source" / "template_with_defaults.txt"
        source = "test.robot"
        self.run_tidy(
            select=[self.FORMATTER_NAME],
            configure=[f"{self.FORMATTER_NAME}.doc_template={template_path}"],
            source=source,
            test_on_version=">=5",
        )
        self.compare_file(source, "template_with_defaults.robot")

    def test_template_with_defaults_relative_path(self):
        template_path = Path(__file__).parent / "source" / "template_with_defaults.txt"
        rel_template_path = get_relative_path(template_path)
        source = "test.robot"
        self.run_tidy(
            select=[self.FORMATTER_NAME],
            configure=[f"{self.FORMATTER_NAME}.doc_template={rel_template_path}"],
            source=source,
            test_on_version=">=5",
        )
        self.compare_file(source, "template_with_defaults.robot")

    # def test_invalid_template_path(self):  # TODO check test error output
    #     template_path = "invalid/path.jinja"
    #     configure = [
    #         f"{self.FORMATTER_NAME}:enabled={True}",
    #         f"{self.FORMATTER_NAME}:doc_template={template_path}"
    #     ]
    #     result = self.run_tidy(
    #         configure=configure,
    #         source="test.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'doc_template' parameter value: '{template_path}'. "
    #         f"The template path does not exist or cannot be found.\n"
    #     )
    #     assert expected_output == result.output

    # def test_invalid_template(self):  # TODO check test error output
    #     template_path = Path(__file__).parent / "source" / "invalid_template.jinja"
    #     rel_template_path = get_relative_path(template_path)
    #     source = "test.robot"
    #     result = self.run_tidy(select=[self.FORMATTER_NAME], confiugre=configure, source=source, exit_code=1)
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'doc_template' parameter value: 'template content'. "
    #         f"Failed to load the template: Unexpected end of template. Jinja was looking for the "
    #         f"following tags: 'endfor' or 'else'. The innermost block that needs to be closed is 'for'.\n"
    #     )
    #     assert expected_output == result.output
