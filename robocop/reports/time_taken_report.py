from timeit import default_timer as timer

from robocop.reports import Report


class TimeTakenReport(Report):
    """
    Report name: ``scan_timer``

    Report that returns Robocop execution time

    Example::

        Scan finished in 0.054s.
    """

    def __init__(self):
        self.name = "scan_timer"
        self.description = "Returns Robocop execution time"
        self.start_time = timer()

    def get_report(self) -> str:
        return f"\nScan finished in {timer() - self.start_time:.3f}s."
