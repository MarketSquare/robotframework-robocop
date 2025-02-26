class RobocopFatalError(ValueError):
    pass


class FileError(RobocopFatalError):
    def __init__(self, source):
        msg = f'File "{source}" does not exist'
        super().__init__(msg)


class InvalidParameterFormatError(RobocopFatalError):
    def __init__(self, name: str):
        super().__init__(f"{name}: Invalid parameter format. Pass parameters using Name.param_name=value syntax.")
