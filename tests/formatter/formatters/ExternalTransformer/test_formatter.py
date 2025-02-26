from pathlib import Path

import pytest

from tests.formatter import FormatterAcceptanceTest


def get_relative_path(abs_path: Path) -> Path:
    cwd = Path.cwd()
    return abs_path.relative_to(cwd)


PARENT_DIR = Path(__file__).parent
EXTERNAL_TRANSFORMER = PARENT_DIR / "ExternalTransformer.py"
EXTERNAL_TRANSFORMER_REL = get_relative_path(EXTERNAL_TRANSFORMER)
DISABLED_TRANSFORMER = PARENT_DIR / "ExternalDisabledTransformer.py"
DISABLED_TRANSFORMER_REL = get_relative_path(DISABLED_TRANSFORMER)
MODULE_TRANSFORMERS = PARENT_DIR / "ExternalTransformers"
MODULE_TRANSFORMERS_REL = get_relative_path(MODULE_TRANSFORMERS)
MODULE_ORDERED_TRANFORMERS = PARENT_DIR / "ExternalTransformersOrdered"


class TestExternalTransformer(FormatterAcceptanceTest):
    FORMATTER_NAME = "ExternalTransformer"

    @pytest.mark.parametrize("external_transformer", [EXTERNAL_TRANSFORMER, EXTERNAL_TRANSFORMER_REL])
    def test_transform_external_transformer(self, external_transformer):
        self.run_tidy(
            select=[str(external_transformer)], configure=[f"{self.FORMATTER_NAME}.param=2"], source="tests.robot"
        )
        self.compare_file("tests.robot")

    @pytest.mark.parametrize("external_transformer", [EXTERNAL_TRANSFORMER, EXTERNAL_TRANSFORMER_REL])
    def test_load_external_transformer(self, external_transformer):
        self.run_tidy(
            custom_formatters=[str(external_transformer)],
            configure=[f"{self.FORMATTER_NAME}.param=2"],
            source="tests.robot",
        )
        self.compare_file("tests.robot", expected_name="tests_with_defaults.robot")

    @pytest.mark.parametrize("disabled_transformer", [DISABLED_TRANSFORMER, DISABLED_TRANSFORMER_REL])
    def test_transform_disabled(self, disabled_transformer):
        self.run_tidy(select=[str(disabled_transformer)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_lowercase.robot")

    @pytest.mark.parametrize("disabled_transformer", [DISABLED_TRANSFORMER, DISABLED_TRANSFORMER_REL])
    def test_load_disabled(self, disabled_transformer):
        self.run_tidy(custom_formatters=[str(disabled_transformer)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_only_defaults.robot")

    @pytest.mark.parametrize("module_path", [MODULE_TRANSFORMERS, MODULE_TRANSFORMERS_REL])
    def test_load_from_module(self, module_path):
        self.run_tidy(custom_formatters=[str(module_path)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_module_load.robot")

    @pytest.mark.parametrize("module_path", [MODULE_TRANSFORMERS, MODULE_TRANSFORMERS_REL])
    def test_load_from_module_using_select(self, module_path):
        self.run_tidy(select=[str(module_path)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_module_transform.robot")

    # FIXME: do not work - but didn't work before migration and was hidden due to duplicated test name
    # @pytest.mark.parametrize("module_path", [MODULE_TRANSFORMERS, MODULE_TRANSFORMERS_REL])
    # def test_load_from_module_and_configure(self, module_path):
    #     self.run_tidy(
    #         custom_formatters=[str(module_path)], configure=["CustomClass2.extra_param=True"], source="tests.robot"
    #     )
    #     self.compare_file("tests.robot", expected_name="tests_module_load_configure.robot")

    @pytest.mark.parametrize("module_path", [MODULE_TRANSFORMERS, MODULE_TRANSFORMERS_REL])
    def test_load_from_module_using_select_and_configure(self, module_path):
        self.run_tidy(select=[str(module_path)], configure=["CustomClass2.extra_param=True"], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_module_transform_configure.robot")

    def test_transform_ordered(self):
        self.run_tidy(select=[str(MODULE_ORDERED_TRANFORMERS)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_module_transform.robot")

    def test_load_ordered(self):
        self.run_tidy(custom_formatters=[str(MODULE_ORDERED_TRANFORMERS)], source="tests.robot")
        self.compare_file("tests.robot", expected_name="tests_module_load.robot")
