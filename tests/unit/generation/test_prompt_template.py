"""
Tests for the prompt template system.
"""

import os
import json
import yaml
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import GenerationError
from src.knowledge_base.generation.prompt_template import PromptTemplate, PromptTemplateManager


class TestPromptTemplate:
    """Tests for the PromptTemplate class."""

    def test_init(self):
        """Test initialization."""
        template = PromptTemplate("Hello, {name}!")
        assert template.template == "Hello, {name}!"
        assert template.template_id is None

        template = PromptTemplate("Hello, {name}!", template_id="greeting")
        assert template.template == "Hello, {name}!"
        assert template.template_id == "greeting"

    def test_format(self):
        """Test formatting a template."""
        template = PromptTemplate("Hello, {name}!")
        result = template.format(name="World")
        assert result == "Hello, World!"

    def test_format_missing_variable(self):
        """Test formatting with a missing variable."""
        template = PromptTemplate("Hello, {name}!")
        with pytest.raises(GenerationError):
            template.format()

    def test_get_required_variables(self):
        """Test getting required variables."""
        template = PromptTemplate("Hello, {name}! Today is {day}.")
        variables = template.get_required_variables()
        assert set(variables) == {"name", "day"}

    def test_str(self):
        """Test string representation."""
        template = PromptTemplate("Hello, {name}!")
        assert str(template) == "Hello, {name}!"


class TestPromptTemplateManager:
    """Tests for the PromptTemplateManager class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return Config()

    def test_init(self, config):
        """Test initialization."""
        manager = PromptTemplateManager(config)
        assert "default_rag" in manager.templates
        assert "default_qa" in manager.templates
        assert "default_summarization" in manager.templates

    def test_get_template(self, config):
        """Test getting a template."""
        manager = PromptTemplateManager(config)
        template = manager.get_template("default_rag")
        assert isinstance(template, PromptTemplate)
        assert template.template_id == "default_rag"

    def test_get_template_not_found(self, config):
        """Test getting a non-existent template."""
        manager = PromptTemplateManager(config)
        with pytest.raises(GenerationError):
            manager.get_template("non_existent")

    def test_add_template(self, config):
        """Test adding a template."""
        manager = PromptTemplateManager(config)
        manager.add_template("test", "This is a {test}.")
        template = manager.get_template("test")
        assert template.template == "This is a {test}."
        assert template.template_id == "test"

    def test_add_template_object(self, config):
        """Test adding a template object."""
        manager = PromptTemplateManager(config)
        template = PromptTemplate("This is a {test}.", template_id="test")
        manager.add_template("test", template)
        retrieved = manager.get_template("test")
        assert retrieved.template == "This is a {test}."
        assert retrieved.template_id == "test"

    def test_remove_template(self, config):
        """Test removing a template."""
        manager = PromptTemplateManager(config)
        manager.add_template("test", "This is a {test}.")
        manager.remove_template("test")
        with pytest.raises(GenerationError):
            manager.get_template("test")

    def test_remove_template_not_found(self, config):
        """Test removing a non-existent template."""
        manager = PromptTemplateManager(config)
        with pytest.raises(GenerationError):
            manager.remove_template("non_existent")

    def test_list_templates(self, config):
        """Test listing templates."""
        manager = PromptTemplateManager(config)
        templates = manager.list_templates()
        assert "default_rag" in templates
        assert "default_qa" in templates
        assert "default_summarization" in templates

    def test_format_template(self, config):
        """Test formatting a template."""
        manager = PromptTemplateManager(config)
        result = manager.format_template("default_rag", query="What is the capital of France?", context="Paris is the capital of France.")
        assert "Paris is the capital of France." in result
        assert "What is the capital of France?" in result

    def test_format_template_not_found(self, config):
        """Test formatting a non-existent template."""
        manager = PromptTemplateManager(config)
        with pytest.raises(GenerationError):
            manager.format_template("non_existent", query="test", context="test")

    def test_load_custom_templates_from_config(self):
        """Test loading custom templates from configuration."""
        config = Config()
        config.generation.prompt_templates = {
            "custom": "This is a {custom} template."
        }
        manager = PromptTemplateManager(config)
        assert "custom" in manager.templates
        template = manager.get_template("custom")
        assert template.template == "This is a {custom} template."

    def test_load_templates_from_directory(self):
        """Test loading templates from a directory."""
        with TemporaryDirectory() as temp_dir:
            # Create JSON template file
            json_path = Path(temp_dir) / "templates.json"
            with open(json_path, "w") as f:
                json.dump({
                    "json_template": "This is a {json} template."
                }, f)

            # Create YAML template file
            yaml_path = Path(temp_dir) / "templates.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump({
                    "yaml_template": "This is a {yaml} template."
                }, f)

            # Create config with template directory
            config = Config()
            config.generation.template_directory = temp_dir

            # Create manager
            manager = PromptTemplateManager(config)

            # Check templates were loaded
            assert "json_template" in manager.templates
            assert "yaml_template" in manager.templates

            # Check template content
            json_template = manager.get_template("json_template")
            assert json_template.template == "This is a {json} template."

            yaml_template = manager.get_template("yaml_template")
            assert yaml_template.template == "This is a {yaml} template."

    def test_save_templates(self):
        """Test saving templates."""
        with TemporaryDirectory() as temp_dir:
            config = Config()
            manager = PromptTemplateManager(config)
            
            # Add a custom template
            manager.add_template("custom", "This is a {custom} template.")
            
            # Save templates to JSON
            json_path = Path(temp_dir) / "templates.json"
            manager.save_templates(json_path)
            
            # Check file exists
            assert json_path.exists()
            
            # Load the file and check content
            with open(json_path, "r") as f:
                templates = json.load(f)
            
            assert "custom" in templates
            assert templates["custom"] == "This is a {custom} template."
            
            # Save templates to YAML
            yaml_path = Path(temp_dir) / "templates.yaml"
            manager.save_templates(yaml_path)
            
            # Check file exists
            assert yaml_path.exists()
            
            # Load the file and check content
            with open(yaml_path, "r") as f:
                templates = yaml.safe_load(f)
            
            assert "custom" in templates
            assert templates["custom"] == "This is a {custom} template."