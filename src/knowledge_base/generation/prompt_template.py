"""
Prompt template system for the knowledge base.

This module provides functionality for creating and managing prompt templates
with variable substitution for use in the generation system.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from string import Formatter

from ..core.config import Config
from ..core.exceptions import GenerationError


class PromptTemplate:
    """A template for generating prompts with variable substitution."""

    def __init__(self, template: str, template_id: Optional[str] = None):
        """Initialize a prompt template.

        Args:
            template: The template string with placeholders for variables.
            template_id: Optional identifier for the template.
        """
        self.template = template
        self.template_id = template_id
        self._validate_template()

    def _validate_template(self) -> None:
        """Validate the template format.

        Raises:
            GenerationError: If the template is invalid.
        """
        try:
            # Extract all field names from the template
            field_names = [fname for _, fname, _, _ in Formatter().parse(self.template) if fname]
            
            # Template is valid if we can parse it
            return
        except Exception as e:
            raise GenerationError(f"Invalid prompt template: {str(e)}")

    def format(self, **kwargs: Any) -> str:
        """Format the template with the provided variables.

        Args:
            **kwargs: Variables to substitute in the template.

        Returns:
            The formatted prompt.

        Raises:
            GenerationError: If formatting fails.
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise GenerationError(f"Missing required variable in prompt template: {str(e)}")
        except Exception as e:
            raise GenerationError(f"Failed to format prompt template: {str(e)}")

    def get_required_variables(self) -> List[str]:
        """Get the list of variables required by this template.

        Returns:
            A list of variable names.
        """
        return [fname for _, fname, _, _ in Formatter().parse(self.template) if fname]

    def __str__(self) -> str:
        """Return the template string.

        Returns:
            The template string.
        """
        return self.template


class PromptTemplateManager:
    """Manages a collection of prompt templates."""

    def __init__(self, config: Config):
        """Initialize the prompt template manager.

        Args:
            config: The system configuration.
        """
        self.config = config
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
        self._load_custom_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        # Default RAG template
        self.templates["default_rag"] = PromptTemplate(
            """Answer the following question based on the provided context. 
If you cannot answer the question based on the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:""",
            template_id="default_rag"
        )

        # Default QA template
        self.templates["default_qa"] = PromptTemplate(
            """Answer the following question:

Question: {query}

Answer:""",
            template_id="default_qa"
        )

        # Default summarization template
        self.templates["default_summarization"] = PromptTemplate(
            """Summarize the following text:

Text:
{context}

Summary:""",
            template_id="default_summarization"
        )

    def _load_custom_templates(self) -> None:
        """Load custom templates from configuration and files."""
        # Load from configuration
        if hasattr(self.config.generation, "prompt_templates") and isinstance(self.config.generation.prompt_templates, dict):
            for template_id, template_str in self.config.generation.prompt_templates.items():
                self.templates[template_id] = PromptTemplate(template_str, template_id=template_id)

        # Load from template directory if specified
        template_dir = getattr(self.config.generation, "template_directory", None)
        if template_dir:
            self._load_templates_from_directory(template_dir)

    def _load_templates_from_directory(self, directory: Union[str, Path]) -> None:
        """Load templates from a directory.

        Args:
            directory: Path to the directory containing template files.
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            return

        # Use explicit file patterns since glob with alternatives may not work as expected
        json_files = list(directory.glob("*.json"))
        yaml_files = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
        
        for file_path in json_files + yaml_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    if file_path.suffix.lower() == ".json":
                        templates = json.load(f)
                    else:  # yaml or yml
                        templates = yaml.safe_load(f)

                if isinstance(templates, dict):
                    for template_id, template_data in templates.items():
                        if isinstance(template_data, str):
                            template_str = template_data
                        elif isinstance(template_data, dict) and "template" in template_data:
                            template_str = template_data["template"]
                        else:
                            continue

                        self.templates[template_id] = PromptTemplate(template_str, template_id=template_id)
            except Exception as e:
                # Log error but continue loading other templates
                print(f"Error loading templates from {file_path}: {str(e)}")

    def get_template(self, template_id: str) -> PromptTemplate:
        """Get a template by ID.

        Args:
            template_id: The template identifier.

        Returns:
            The prompt template.

        Raises:
            GenerationError: If the template is not found.
        """
        if template_id not in self.templates:
            raise GenerationError(f"Prompt template not found: {template_id}")
        return self.templates[template_id]

    def add_template(self, template_id: str, template: Union[str, PromptTemplate]) -> None:
        """Add a new template.

        Args:
            template_id: The template identifier.
            template: The template string or PromptTemplate object.
        """
        if isinstance(template, str):
            template = PromptTemplate(template, template_id=template_id)
        self.templates[template_id] = template

    def remove_template(self, template_id: str) -> None:
        """Remove a template.

        Args:
            template_id: The template identifier.

        Raises:
            GenerationError: If the template is not found.
        """
        if template_id not in self.templates:
            raise GenerationError(f"Prompt template not found: {template_id}")
        del self.templates[template_id]

    def list_templates(self) -> List[str]:
        """List all available template IDs.

        Returns:
            A list of template IDs.
        """
        return list(self.templates.keys())

    def format_template(self, template_id: str, **kwargs: Any) -> str:
        """Format a template with the provided variables.

        Args:
            template_id: The template identifier.
            **kwargs: Variables to substitute in the template.

        Returns:
            The formatted prompt.
        """
        template = self.get_template(template_id)
        return template.format(**kwargs)

    def save_templates(self, file_path: Union[str, Path]) -> None:
        """Save all templates to a file.

        Args:
            file_path: Path to save the templates.

        Raises:
            GenerationError: If saving fails.
        """
        try:
            file_path = Path(file_path)
            templates_dict = {
                template_id: template.template
                for template_id, template in self.templates.items()
            }

            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    json.dump(templates_dict, f, indent=2)
                else:  # yaml or yml
                    yaml.dump(templates_dict, f, default_flow_style=False)
        except Exception as e:
            raise GenerationError(f"Failed to save templates: {str(e)}")