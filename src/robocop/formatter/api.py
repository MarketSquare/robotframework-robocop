"""
Methods for transforming Robot Framework ast model programmatically.
"""

from __future__ import annotations

from pathlib import Path

from robotidy import app, disablers, files
from robotidy.config import MainConfig, RawConfig


def get_robotidy(src: str, output: str | None, ignore_git_dir: bool = False, **kwargs):
    config = RawConfig(**kwargs)
    config_file = files.find_source_config_file(Path(src), ignore_git_dir)
    if config_file:
        config_dict = files.read_pyproject_config(config_file)
        config = config.from_config_file(config_dict, config_file)
    main_config = MainConfig(config)
    main_config.default_loaded.overwrite = False
    main_config.default_loaded.show_diff = False
    main_config.default_loaded.verbose = False
    main_config.default_loaded.check = False
    main_config.default_loaded.force_order = False
    main_config.default_loaded.output = output
    return app.Robotidy(main_config)


def transform_model(model, root_dir: str, output: str | None = None, **kwargs) -> str | None:
    """
    :param model: The model to be transformed.
    :param root_dir: Root directory. Configuration file is searched based
    on this directory or one of its parents.
    :param output: Path where transformed model should be saved
    :param kwargs: Default values for global formatting parameters
    such as ``spacecount``, ``startline`` and ``endline``.
    :return: The transformed model converted to string or None if no transformation took place.
    """
    robotidy_class = get_robotidy(root_dir, output, **kwargs)
    disabler_finder = disablers.RegisterDisablers(
        robotidy_class.config.formatting.start_line, robotidy_class.config.formatting.end_line
    )
    disabler_finder.visit(model)
    if disabler_finder.is_disabled_in_file(disablers.ALL_TRANSFORMERS):
        return None
    diff, _, new_model = robotidy_class.transform(model, disabler_finder.disablers)
    if not diff:
        return None
    return new_model.text
