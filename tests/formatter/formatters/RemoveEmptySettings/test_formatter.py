import pytest

from tests.formatter import FormatterAcceptanceTest


class TestRemoveEmptySettings(FormatterAcceptanceTest):
    FORMATTER_NAME = "RemoveEmptySettings"

    @pytest.mark.parametrize("source", ["empty", "overwritten"])
    @pytest.mark.parametrize("work_mode", ["always", "overwritten_ok"])
    @pytest.mark.parametrize("more_explicit", ["more_explicit", "no_explicit"])
    def test_modes(self, source, work_mode, more_explicit):
        configure = []
        if work_mode != "overwritten_ok":
            configure.append(f"{self.FORMATTER_NAME}.work_mode={work_mode}")
        if more_explicit != "more_explicit":
            configure.append(f"{self.FORMATTER_NAME}.more_explicit=False")
        self.compare(
            source=f"{source}.robot",
            expected=f"{source}_{work_mode}_{more_explicit}.robot",
            configure=configure,
        )

    def test_disablers(self):
        self.compare(source="disablers.robot", not_modified=True)
