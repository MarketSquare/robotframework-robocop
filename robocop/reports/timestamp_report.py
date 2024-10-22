from datetime import datetime, timezone
from warnings import warn

import pytz

import robocop.exceptions
import robocop.reports


class TimestampReport(robocop.reports.Report):
    """
    **Report name**: ``timestamp``

    Report that returns Robocop execution timestamp.
    Timestamp follows local time in format of
    ``Year-Month-Day Hours(24-hour clock):Minutes:Seconds ±hh:mm UTC offset`` as default.

    Example::

        Reported: 2022-07-10 21:25:00 +0300

    Both of default values, ``timezone`` and ``format`` can be configured by
    ``-c/--configure`` and ``timestamp:timezone:"<timezone name>"`` and/or ``timestamp:format:"<format string>"``::

        robocop --configure timestamp:timezone:"Europe/Paris" --configure timestamp:format:"%Y-%m-%d %H:%M:%S %Z %z"

    This yields following timestamp report::

         Reported: 2022-07-10 20:38:10 CEST +0200

    For timezone names,
    see `here <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_.

    For timestamp formats,
    see `datetime format codes <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`_.

    Useful configurations::

        Local time to ISO 8601 format:
        robocop --configure timestamp:format:"%Y-%m-%dT%H:%M:%S%z"

        UTC time:
        robocop --configure timestamp:timezone:"UTC" --configure timestamp:format:"%Y-%m-%dT%H:%M:%S %Z %z"

        Timestamp with high precision:
        robocop --configure timestamp:format:"%Y-%m-%dT%H:%M:%S.%f %z"

        12-hour clock:
        robocop --configure timestamp:format:"%Y-%m-%d %I:%M:%S %p %Z %z"

        More human-readable format 'On 10 July 2022 07:26:24 +0300':
        robocop --configure timestamp:format:"On %d %B %Y %H:%M:%S %z"

    """

    def __init__(self):
        self.name = "timestamp"
        self.description = "Returns Robocop execution timestamp."
        self.timezone = "local"
        self.format = "%Y-%m-%d %H:%M:%S %z"

    def configure(self, name, value):
        if name == "timezone":
            self.timezone = value
        elif name == "format":
            if value:
                self.format = value
            else:
                warn("Empty format string for `timestamp` report does not make sense. Default format used.")
        else:
            super().configure(name, value)

    def get_report(self) -> str:
        return f"\nReported: {self._get_timestamp()}"

    def _get_timestamp(self) -> str:
        try:
            if self.timezone == "local":
                timezone_code = datetime.now(timezone.utc).astimezone().tzinfo
            else:
                timezone_code = pytz.timezone(self.timezone)
            return datetime.now(timezone_code).strftime(self.format)
        except pytz.exceptions.UnknownTimeZoneError as err:
            raise robocop.exceptions.ConfigGeneralError(
                f"Provided timezone '{self.timezone}' for report '{getattr(self, 'name')}' is not valid. "
                "Use timezone names like `Europe\\Helsinki`."
                "See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zone"
            ) from err
