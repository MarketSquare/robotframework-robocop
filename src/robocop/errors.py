class RobocopFatalError(ValueError):
    pass


class FileError(RobocopFatalError):
    def __init__(self, source):
        msg = f'File "{source}" does not exist'
        super().__init__(msg)
