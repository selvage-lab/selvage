# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing

```bash
# Run unit and integration tests
pytest tests/

# Run E2E tests (requires testcontainers and docker)
pytest e2e/

# Run LLM evaluation tests
pytest llm_eval/

# Run tests with coverage
pytest tests/ --cov

# Run specific test patterns
pytest tests/test_llm_gateway.py -v
```

### Code Quality

```bash
# Format code with ruff
ruff format .

# Run linting with ruff
ruff check .

# Fix auto-fixable linting issues
ruff check . --fix
```

### Package Management

```bash
# Install for development
pip install -e .[dev]

# Install with E2E test dependencies
pip install -e .[dev,e2e]

# Build package
python -m build

# Upload to PyPI (requires twine)
twine upload dist/*
```

### Running the Application

```bash
# Basic code review
selvage review

# Review staged changes
selvage review --staged

# Review with specific model
selvage review --model claude-sonnet-4-thinking

# Launch UI to view results
selvage view

# Set API keys
selvage --set-openai-key
selvage --set-claude-key
selvage --set-gemini-key
```

## Architecture Overview

Selvage is an LLM-based code review tool with a modular architecture:

### Core Components

**CLI Interface** (`selvage/cli.py`)

- Main entry point using Click framework
- Handles command parsing and user interaction
- Manages API key setup and configuration

**LLM Gateway System** (`selvage/src/llm_gateway/`)

- `gateway_factory.py`: Factory pattern for creating LLM clients
- `base_gateway.py`: Abstract base class for all LLM providers
- Provider-specific gateways: `openai_gateway.py`, `claude_gateway.py`, `google_gateway.py`
- Handles API communication, token counting, and cost estimation

**Diff Processing** (`selvage/src/diff_parser/`)

- `parser.py`: Git diff parsing and processing
- `models/`: Data models for diff representation (DiffResult, FileDiff, Hunk)
- Converts git diff output into structured data for LLM analysis

**Prompt System** (`selvage/src/utils/prompts/`)

- `prompt_generator.py`: Creates structured prompts for LLM review
- `models/`: Prompt data models (ReviewPrompt, SystemPrompt, UserPrompt)
- Supports both diff-only and full-file context modes

**Configuration Management** (`selvage/src/config.py`)

- Platform-specific config directory handling
- API key management (environment variables take precedence)
- User preferences storage (default model, debug mode, etc.)

### Data Flow

1. **Git Diff Extraction**: `GitDiffUtility` extracts changes from repository
2. **Diff Parsing**: `DiffParser` converts raw diff into structured `DiffResult`
3. **Prompt Generation**: `PromptGenerator` creates context-aware prompts
4. **LLM Review**: Gateway sends prompts to configured AI model
5. **Result Processing**: Response is formatted and saved as review log
6. **UI Display**: Streamlit interface shows results with markdown/JSON views

### Key Design Patterns

- **Factory Pattern**: `GatewayFactory` for LLM provider instantiation
- **Strategy Pattern**: Different diff modes (staged, unstaged, target branch/commit)
- **Template Method**: Base gateway class with provider-specific implementations
- **Configuration**: Environment variables override file-based settings

### Model Support

The tool supports multiple AI providers:

- **OpenAI**: GPT-4o, GPT-4.1, o4-mini variants
- **Anthropic**: Claude Sonnet-4, Claude Sonnet-4-thinking
- **Google**: Gemini 2.5 Pro, Gemini 2.5 Flash

Model configuration is centralized in `selvage/src/model_config.py` with provider-specific settings.

## Testing Strategy

- **Unit Tests** (`tests/`): Component-level testing
- **E2E Tests** (`e2e/`): Full workflow testing with Docker containers
- **LLM Evaluation** (`llm_eval/`): AI model response quality assessment using DeepEval

## Important Notes

- The codebase uses Python 3.10+ with type hints throughout
- Configuration follows platform conventions (XDG on Linux, Application Support on macOS)
- All user-facing text is in Korean (this is intentional for the target audience)
- The tool maintains review logs in structured JSON format for audit trails
- API keys are validated and securely stored with appropriate file permissions
