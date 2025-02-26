import functools

try:
    import rich_click as click
except ImportError:
    import click

from robocop.formatter import exceptions


def catch_exceptions(func):
    """Catch exceptions and print user-friendly message for common issues"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # noqa: ANN202
        if not func:
            return functools.partial(catch_exceptions)
        try:
            return func(*args, **kwargs)
        except (click.exceptions.ClickException, click.exceptions.Exit):
            raise
        except Exception as err:
            message = (
                "\nFatal exception occurred. You can create an issue at "
                "https://github.com/MarketSquare/robotframework-tidy/issues . Thanks!"
            )
            err.args = (str(err.args[0]) + message,) + err.args[1:]
            raise err  # noqa: TRY201

    return wrapper


def optional_rich(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # noqa: ANN202
        try:
            return func(*args, **kwargs)
        except ImportError as err:
            raise exceptions.MissingOptionalRichDependencyError from err

    return wrapper
