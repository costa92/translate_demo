# Prompt Template System

The prompt template system provides a flexible way to create and manage prompt templates for the generation system. Templates can be defined in configuration, code, or external files, and can be used to generate prompts for different use cases.

## Overview

The prompt template system consists of two main components:

1. **PromptTemplate**: A class that represents a single prompt template with variable substitution.
2. **PromptTemplateManager**: A class that manages a collection of prompt templates.

## Using Prompt Templates

### Basic Usage

```python
from src.knowledge_base.generation.prompt_template import PromptTemplate

# Create a template
template = PromptTemplate("Hello, {name}!")

# Format the template
result = template.format(name="World")
print(result)  # Output: Hello, World!
```

### Using the Template Manager

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.generation.prompt_template import PromptTemplateManager

# Create a configuration
config = Config()

# Create a template manager
manager = PromptTemplateManager(config)

# Get a default template
template = manager.get_template("default_rag")

# Format the template
result = manager.format_template(
    "default_rag",
    query="What is the capital of France?",
    context="Paris is the capital of France."
)
print(result)
```

### Adding Custom Templates

```python
# Add a template directly
manager.add_template("custom", "This is a {custom} template.")

# Format the custom template
result = manager.format_template("custom", custom="test")
print(result)  # Output: This is a test template.
```

## Configuration

The prompt template system can be configured in several ways:

### Direct Template

You can specify a direct template in the configuration:

```python
config.generation.prompt_template = "Q: {query}\nC: {context}"
```

### Template ID

You can specify a template ID to use from the template manager:

```python
config.generation.template_id = "default_rag"
```

### Custom Templates

You can define custom templates in the configuration:

```python
config.generation.prompt_templates = {
    "custom": "This is a {custom} template."
}
```

### Template Directory

You can specify a directory containing template files:

```python
config.generation.template_directory = "path/to/templates"
```

Template files can be in JSON or YAML format:

**templates.json**:
```json
{
  "json_template": "This is a {json} template."
}
```

**templates.yaml**:
```yaml
yaml_template: This is a {yaml} template.
```

## Default Templates

The system provides several default templates:

### default_rag

```
Answer the following question based on the provided context. 
If you cannot answer the question based on the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:
```

### default_qa

```
Answer the following question:

Question: {query}

Answer:
```

### default_summarization

```
Summarize the following text:

Text:
{context}

Summary:
```

## Integration with Generator

The prompt template system is integrated with the Generator class:

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk
from src.knowledge_base.generation.generator import Generator

# Create a configuration
config = Config()

# Set the template ID
config.generation.template_id = "default_rag"

# Create a generator
generator = Generator(config)

# Generate a response
chunks = [TextChunk(id="1", text="Paris is the capital of France.", document_id="doc1", metadata={})]
response = await generator.generate("What is the capital of France?", chunks)
print(response)
```

## Advanced Usage

### Saving Templates

You can save templates to a file:

```python
manager.save_templates("templates.json")
```

### Required Variables

You can get the list of variables required by a template:

```python
template = manager.get_template("default_rag")
variables = template.get_required_variables()
print(variables)  # Output: ['context', 'query']
```

### Error Handling

The system provides comprehensive error handling:

```python
try:
    result = manager.format_template("non_existent", query="test")
except GenerationError as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Use descriptive template IDs**: Choose template IDs that clearly indicate the purpose of the template.
2. **Include all required variables**: Ensure that all required variables are provided when formatting a template.
3. **Use consistent variable names**: Use consistent variable names across templates for similar concepts.
4. **Organize templates by purpose**: Group templates by their purpose or use case.
5. **Document templates**: Include comments or documentation for complex templates.
6. **Test templates**: Test templates with different inputs to ensure they work as expected.
7. **Use fallbacks**: Implement fallback mechanisms for when a template is not found or cannot be formatted.