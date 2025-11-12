from pathlib import Path

from jinja2 import Template

from robocop import __version__


def render_template(template_path: Path, **values) -> str:
    tpl_text = template_path.read_text(encoding="utf-8")
    tpl = Template(tpl_text)
    return tpl.render(**values)


def define_env(env):
    """Define functions available in Markdown as Jinja functions."""

    @env.macro
    def enable_hint(formatter) -> str:
        tpl_path = Path(env.project_dir) / "docs" / "formatter" / "formatters" / "enable_hint.md.jinja"
        return render_template(tpl_path, formatter=formatter)

    @env.macro
    def configure_hint(formatter) -> str:
        tpl_path = Path(env.project_dir) / "docs" / "formatter" / "formatters" / "configure_hint.md.jinja"
        return render_template(tpl_path, formatter=formatter)

    @env.macro
    def robocop_version() -> str:
        return __version__
