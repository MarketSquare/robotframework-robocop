def reload_robocop_rules():
    """Reload imported Robocop modules.

    Robocop get rules by importing them from Python files. When we're configuring them, rules attributes like enabled
    status changes.
    Consecutive tests reuse the same loaded module (
    """
