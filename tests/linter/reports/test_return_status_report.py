import pytest

from robocop.linter.reports.return_status_report import ReturnStatusReport


class TestReturnStatus:
    @pytest.mark.parametrize(
        ("param", "configuration", "quality_gates"),
        [
            ("quality_gate", "", {"E": 0, "W": 0, "I": -1}),
            ("quality_gates", "", {"E": 0, "W": 0, "I": -1}),
            ("quality_gates", "e=-1:w=-1:i=-1", {"E": -1, "W": -1, "I": -1}),
            ("quality_gates", "e=-1:w=-1:i=-1:r=0", {"E": -1, "W": -1, "I": -1}),
            ("quality_gates", "i=0", {"E": 0, "W": 0, "I": 0}),
            ("quality_gates", "E=100:W=100:I=100", {"E": 100, "W": 100, "I": 100}),
        ],
    )
    def test_quality_gates_configuration(self, param, configuration, quality_gates, config):
        report = ReturnStatusReport(config)
        report.configure(param, configuration)
        assert report.quality_gate == quality_gates

    @pytest.mark.parametrize(
        ("quality_gates", "return_status"),
        [
            ("", 20),
            ("e=-1", 10),
            ("i=0", 30),
            ("e=0:w=0:i=-1", 20),
            ("e=0:w=0:i=0", 30),
            ("e=0:w=-1:i=0", 20),
            ("e=-1:w=0:i=0", 20),
            ("e=-1:w=-1:i=-1", 0),
            ("e=-2:w=-2:i=-2", 0),
            ("e=10:w=10:i=10", 0),
            ("e=20:w=20:i=20", 0),
        ],
    )
    def test_return_status_with_quality_gates(
        self, error_msg, warning_msg, info_msg, quality_gates, return_status, config
    ):
        report = ReturnStatusReport(config)
        report.configure("quality_gates", quality_gates)
        for _ in range(10):
            report.add_message(error_msg)
            report.add_message(warning_msg)
            report.add_message(info_msg)
        report.get_report()
        assert report.return_status == return_status
