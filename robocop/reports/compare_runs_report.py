import robocop.reports


class CompareRunsReport(robocop.reports.Report):
    """
    **Report name**: ``compare_runs``

    Special report that is used to enhance other reports output with the comparison to the previous run results.

    This report is not included in the default reports. The ``--reports all`` option will not enable this report.
    You can still enable it using report name directly: ``--reports compare_runs`` or ``--reports all,compare_runs``.
    """

    DEFAULT = False

    def __init__(self):
        self.name = "compare_runs"
        self.description = "Compare reports between two Robocop runs."
