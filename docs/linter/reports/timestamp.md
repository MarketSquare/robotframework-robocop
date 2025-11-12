# Timestamp

Report name: **timestamp**

Available in ``all``: Yes

Report that prints Robocop execution timestamp.

Timestamp follows local time in the format of ``Year-Month-Day Hours(24-hour clock):Minutes:Seconds ±hh:mm UTC offset``
as default.

Example:

```text
Reported: 2022-07-10 21:25:00 +0300
```

Enable with:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports timestamp
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "timestamp"
    ]
    ```

You can also enable it by using ``all``  which enables all reports that supports ``all`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports all
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "all"
    ]
    ```

## Configuration

### ``Timezone``

Configure timezone to be used in timestamp report with ``timezone`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports timestamp --configure timestamp.timezone="Europe/Paris"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "timestamp"
    ]
    configure = [
        "timestamp.timezone=Europe/Paris"
    ]
    ```

For timezone names, see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.

### ``Format``

Configure a timestamp format with ``format`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop check --reports timestamp --configure timestamp.format="%Y-%m-%d %H:%M:%S %Z %z"
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.lint]
    reports = [
        "timestamp"
    ]
    configure = [
        "timestamp.format=%Y-%m-%d %H:%M:%S %Z %z"
    ]
    ```

For timestamp formats, see [datetime format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).

???+ note "Useful configurations"

    Local time to ISO 8601 format:
    ```bash
    robocop check --configure timestamp.format="%Y-%m-%dT%H:%M:%S%z"
    ```

    UTC time:
    ```bash
    robocop check --configure timestamp.timezone:"UTC" --configure timestamp.format="%Y-%m-%dT%H:%M:%S %Z %z"
    ```

    Timestamp with high precision:
    ```bash
    robocop check --configure timestamp.format="%Y-%m-%dT%H:%M:%S.%f %z"
    ```

    12-hour clock:
    ```bash
    robocop check --configure timestamp.format="%Y-%m-%d %I:%M:%S %p %Z %z"
    ```

    More human-readable format 'On 10 July 2022 07:26:24 +0300':
    ```bash
    robocop check --configure timestamp.format="On %d %B %Y %H:%M:%S %z"
    ```
