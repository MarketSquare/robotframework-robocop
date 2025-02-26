try:
    from rich.console import Console
except ImportError:  # Fails on vendored-in LSP plugin

    class Console:
        @staticmethod
        def print(msg, *args, **kwargs):
            print(
                "It looks line you have rich module uninstalled. "
                "Install it to be able to use robotidy in the cli mode."
            )
            print(msg)


console = Console()
