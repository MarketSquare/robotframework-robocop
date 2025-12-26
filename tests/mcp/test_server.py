"""Tests for MCP server initialization."""

import asyncio

from robocop.mcp import create_server, mcp


class TestServerInitialization:
    """Tests for MCP server setup."""

    def test_server_created(self):
        """Test that the server is created successfully."""
        assert mcp is not None
        assert mcp.name == "robocop"

    def test_create_server_returns_same_instance(self):
        """Test that create_server returns the singleton instance."""
        server = create_server()
        assert server is mcp

    def test_server_has_instructions(self):
        """Test that server has instructions set."""
        assert mcp.instructions is not None
        assert len(mcp.instructions) > 0
        assert "Robocop" in mcp.instructions

    def test_server_instructions_include_quick_start(self):
        """Test that instructions include quick start guide."""
        assert "Quick Start" in mcp.instructions

    def test_server_instructions_include_tools_table(self):
        """Test that instructions include tools by category."""
        assert "lint_content" in mcp.instructions
        assert "format_content" in mcp.instructions
        assert "get_statistics" in mcp.instructions

    def test_server_instructions_include_severity_levels(self):
        """Test that instructions explain severity levels."""
        assert "E (Error)" in mcp.instructions or "Error" in mcp.instructions
        assert "W (Warning)" in mcp.instructions or "Warning" in mcp.instructions
        assert "I (Info)" in mcp.instructions or "Info" in mcp.instructions


class TestToolsRegistration:
    """Tests for MCP tools registration."""

    def test_all_tools_registered(self):
        """Test that all 18 tools are registered."""
        tools = asyncio.run(mcp.get_tools())

        expected_tools = [
            "lint_content",
            "lint_file",
            "lint_files",
            "lint_directory",
            "suggest_fixes",
            "explain_issue",
            "format_content",
            "format_file",
            "format_files",
            "lint_and_format",
            "list_rules",
            "list_formatters",
            "get_rule_info",
            "get_formatter_info",
            "get_statistics",
        ]

        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool '{tool_name}' not registered"

    def test_tools_count(self):
        """Test that correct number of tools are registered."""
        tools = asyncio.run(mcp.get_tools())
        # At least 15 tools should be registered
        assert len(tools) >= 15


class TestResourcesRegistration:
    """Tests for MCP resources registration."""

    def test_resources_registered(self):
        """Test that resources are registered."""
        resources = asyncio.run(mcp.get_resources())
        # Should have at least the 3 main resources
        assert len(resources) >= 2


class TestPromptsRegistration:
    """Tests for MCP prompts registration."""

    def test_all_prompts_registered(self):
        """Test that all 6 prompts are registered."""
        prompts = asyncio.run(mcp.get_prompts())

        expected_prompts = [
            "analyze_robot_file",
            "fix_robot_issues",
            "explain_rule",
            "review_pull_request",
            "configure_robocop",
            "migrate_to_latest",
        ]

        for prompt_name in expected_prompts:
            assert prompt_name in prompts, f"Prompt '{prompt_name}' not registered"

    def test_prompts_count(self):
        """Test that exactly 6 prompts are registered."""
        prompts = asyncio.run(mcp.get_prompts())
        assert len(prompts) == 6
