"""
Robocop plugins.

Plugins allow to package and distribute custom rules, formatters and configuration files as a Python package.
A plugin is registered using the ``robocop.plugins`` entry point group::

    [project.entry-points."robocop.plugins"]
    example = "example_plugin.path.to.dir"

The entry point name (``example``) becomes the plugin namespace and the value points to an importable Python
package that contains the plugin resources. Resources are referenced in the configuration using the
``<plugin_name>.<path.inside.the.plugin>`` syntax, for example ``example.rules`` or ``example.config.strict``.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from robocop import exceptions

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

ENTRY_POINT_GROUP = "robocop.plugins"
"""Name of the entry point group used to register Robocop plugins."""


class UnknownPluginError(exceptions.FatalError):
    def __init__(self, plugin_name: str, reference: str, plugins: list[str]) -> None:
        from robocop.linter.utils.misc import RecommendationFinder  # noqa: PLC0415

        if plugins:
            similar = RecommendationFinder().find_similar(plugin_name, plugins)
            known = similar or f" Installed plugins: {', '.join(sorted(plugins))}."
        else:
            known = " There are no Robocop plugins installed."
        super().__init__(f"Plugin '{plugin_name}' used in '{reference}' is not installed.{known}")


class InvalidPluginError(exceptions.FatalError):
    def __init__(self, plugin_name: str, module_path: str, error: str) -> None:
        super().__init__(f"Failed to load plugin '{plugin_name}' from '{module_path}': {error}")


@dataclass(frozen=True)
class Plugin:
    """Robocop plugin registered with the ``robocop.plugins`` entry point."""

    name: str
    module_path: str

    @property
    def path(self) -> Path:
        """Filesystem location of the plugin package."""
        module = self.load()
        if module_paths := list(getattr(module, "__path__", [])):
            return Path(module_paths[0])
        module_file = getattr(module, "__file__", None)
        if module_file is None:
            raise InvalidPluginError(self.name, self.module_path, "cannot determine the location of the plugin")
        return Path(module_file).parent

    def load(self) -> ModuleType:
        try:
            return import_module(self.module_path)
        except ImportError as err:
            raise InvalidPluginError(self.name, self.module_path, str(err)) from None


class PluginRegistry:
    """Container with all Robocop plugins discovered in the current environment."""

    def __init__(self, plugins: dict[str, Plugin]) -> None:
        self.plugins = plugins

    @classmethod
    def discover(cls) -> PluginRegistry:
        plugins: dict[str, Plugin] = {}
        for entry_point in entry_points(group=ENTRY_POINT_GROUP):
            if entry_point.name in plugins:
                typer.echo(
                    f"Robocop plugin '{entry_point.name}' is registered more than once. "
                    f"Using '{plugins[entry_point.name].module_path}' and ignoring '{entry_point.value}'.",
                    err=True,
                )
                continue
            plugins[entry_point.name] = Plugin(name=entry_point.name, module_path=entry_point.value)
        return cls(plugins)

    def __contains__(self, name: str) -> bool:
        return name in self.plugins

    def __iter__(self) -> Iterator[Plugin]:
        return iter(sorted(self.plugins.values(), key=lambda plugin: plugin.name))

    def __len__(self) -> int:
        return len(self.plugins)

    def get(self, reference: str) -> tuple[Plugin, str] | None:
        """
        Split the reference into the plugin and the path inside the plugin.

        Returns:
            Tuple with the plugin and the remaining, dot separated path, or None if the reference does not start
            with a name of the installed plugin.

        """
        plugin_name, _, rest = reference.partition(".")
        plugin = self.plugins.get(plugin_name)
        if plugin is None:
            return None
        return plugin, rest

    def resolve_module(self, reference: str) -> str | None:
        """
        Resolve the plugin reference to an importable module path.

        ``example.rules`` is resolved to ``example_plugin.path.to.dir.rules``.

        Returns:
            Importable module path, or None if the reference does not point to an installed plugin.

        """
        resolved = self.get(reference)
        if resolved is None:
            return None
        plugin, rest = resolved
        return f"{plugin.module_path}.{rest}" if rest else plugin.module_path

    def resolve_path(self, reference: str, suffix: str) -> Path | None:
        """
        Resolve the plugin reference to a path to the file inside the plugin.

        ``example.config.strict`` is resolved to ``<plugin directory>/config/strict.toml``.

        Returns:
            Path to the file inside the plugin, or None if the reference does not point to an installed plugin.

        """
        resolved = self.get(reference)
        if resolved is None:
            return None
        plugin, rest = resolved
        if not rest:
            raise exceptions.ConfigurationError(
                f"Invalid plugin reference: '{reference}'. "
                f"Expected '{plugin.name}.<path.to.file>' pointing to a file inside the plugin."
            )
        *parents, name = rest.split(".")
        return plugin.path.joinpath(*parents, f"{name}{suffix}")


@lru_cache(maxsize=1)
def get_plugins() -> PluginRegistry:
    """
    Return the registry with all installed Robocop plugins.

    Plugins are discovered only once and the result is cached. Use ``get_plugins.cache_clear()`` to force
    rediscovery (for example in the tests).

    Returns:
        Registry with the installed plugins.

    """
    return PluginRegistry.discover()


def resolve_module_reference(reference: str) -> str | None:
    """
    Resolve the plugin reference to an importable module path.

    Returns:
        Importable module path, or None if the reference does not point to an installed plugin.

    """
    return get_plugins().resolve_module(reference)


def resolve_path_reference(reference: str, suffix: str = ".toml") -> Path:
    """
    Resolve the plugin reference to a path to the file inside the plugin.

    Raises ``UnknownPluginError`` if the plugin is not installed.

    Returns:
        Path to the file inside the plugin.

    """
    plugins = get_plugins()
    path = plugins.resolve_path(reference, suffix)
    if path is None:
        plugin_name = reference.partition(".")[0]
        raise UnknownPluginError(plugin_name, reference, list(plugins.plugins))
    return path
