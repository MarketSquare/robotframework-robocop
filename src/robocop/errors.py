import typer
from rich.console import Console


class FatalError(typer.Exit):
    def __init__(self, msg: str):
        console = Console(stderr=True)
        console.print(f"[red]{self.__class__.__name__}[/red]: {msg}")
        super().__init__(code=2)


class RobocopFatalError(ValueError):
    pass


class InvalidParameterFormatError(RobocopFatalError):
    def __init__(self, name: str):
        super().__init__(f"{name}: Invalid parameter format. Pass parameters using Name.param_name=value syntax.")
