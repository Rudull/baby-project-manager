---
name: python-best-practices
description: Core Python development principles for robust, type-safe, and maintainable code.
---

# Python Best Practices

This skill provides Python development standards for the DesignBox project, focused on robust, type-safe, maintainable code.

## Module Structure
- **Focused files**: Keep one clear purpose per module. Split modules when they grow beyond roughly 300 lines.
- **Public API**: Use `__init__.py` to expose only the symbols that are meant to be imported by other modules.
- **Internal details**: Use `_` prefixes or `_internal.py` modules for private implementation details.

## Type-First Development
1. **Models first**: Define `dataclasses`, typed dictionaries, or Pydantic models before implementing business logic.
2. **Function signatures**: Use complete type hints for parameters and return values.
3. **Validation**: Validate data at system boundaries, such as JSON loading, user input, database rows, or external API responses.

## Functional Patterns
- **Immutability**: Prefer `@dataclass(frozen=True)` for value objects when mutation is not required.
- **Comprehensions**: Prefer list and dictionary comprehensions over explicit append loops when they improve readability.
- **Pure functions**: Avoid unnecessary mutable class-level state. Prefer functions that transform inputs into outputs.

## Error Handling and Exceptions
- **Explicit failure**: Log descriptive errors. Never silence exceptions without a documented reason.
- **Context**: Use `raise ... from err` to preserve tracebacks when wrapping exceptions.
- **pathlib**: Prefer `pathlib.Path` and context managers (`with`) for file I/O.

## Golden Rule
"Make illegal states unrepresentable." Design data structures and types so invalid states are hard or impossible to construct.
