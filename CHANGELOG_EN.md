# Change Log

## [0.4.0] - 2026-02-13

### Added

#### feat: Agent-Delegated Review Mode (get_review_context MCP Tool)

**Core Changes**

- **New get_review_context tool**: Returns structured review context (diff + Smart Context + system prompt) so host agents (Claude Code, Cursor, Antigravity) can perform code reviews using their own LLM without requiring an API key
- **Large context splitting**: When review context exceeds size limit, stores locally and supports per-file retrieval via `get_file_review_context`
- **Claude Code plugin**: Added `.claude/skills/review/SKILL.md` skill and `.claude/agents/selvage-reviewer.md` agent definitions

**Detailed Implementation**

- **ReviewContextResult model**: Pydantic response model containing system_prompt, review_targets, output_format, and metadata
- **Context engine separation**: Extracted prompt generation and context extraction logic from the existing LLM call pipeline for reuse
- **DelegatedContextStore**: Local file storage for large diff contexts with per-file retrieval and TTL-based cleanup (60 minutes)
- **Review tool docstring improvements**: Added guidance to use `get_review_context` as an alternative when no API key is available

## [0.3.0] - 2026-01-28

### Added

#### feat: Latest AI Model Updates and MCP Stability Improvements

**Core Changes**

- **Latest Model Support**: Added GPT-5.2-Codex (OpenAI), Claude Opus 4.5 (Anthropic), MiniMax M2.1, GLM-4.7, and other cutting-edge AI models
- **Simplified Model Configuration**: Removed date suffixes and `-thinking` variants from Claude models, enabled thinking mode by default
- **Enhanced MCP Protocol Protection**: Improved output stream management to prevent stdout pollution
- **High Reasoning Mode Activation**: Applied high reasoning settings to all major models

**Detailed Implementation**

- **Model Upgrades**:
  - `gpt-5`, `gpt-5-high`, `gpt-5-mini` → `gpt-5.2-codex` (reasoning_effort: high)
  - `gemini-2.5-pro/flash` → `gemini-3-pro/flash`
  - `claude-sonnet-4.5-20250929`, `claude-sonnet-4.5-20250929-thinking` → `claude-sonnet-4.5` (thinking default)
  - `claude-opus-4.5-20251101` → `claude-opus-4.5` (thinking default)
- **MCP Server Improvements**:
  - Added FastMCP `show_banner=False` option
  - Redirected warnings to stderr
  - Introduced lazy initialization pattern for BaseConsole (Proxy pattern)
  - Improved MCP mode awareness in logging system
- **Enhanced Reasoning Settings**:
  - `gpt-5.2-codex`: reasoning_effort "high"
  - `minimax-m2.1`: reasoning.max_tokens 16000
  - `glm-4.7`: thinking.type "enabled", max_tokens 16000
  - `claude-*`: budget_tokens 32000

### Breaking Changes

- Removed legacy model names (`gpt-5`, `gpt-5-mini`, `gemini-2.5-flash`, etc.)
- Removed date suffixes from Claude model names (`claude-sonnet-4.5-20250929` → `claude-sonnet-4.5`)

## [0.2.0] - 2025-11-17

### Added

#### feat: claude-sonnet-4.5 support and large context trigger improvements

**Core Changes**

- **claude-sonnet-4.5 integration**: Added the latest Claude Sonnet 4.5 model to the catalog to boost reasoning quality and review fidelity on Sonnet-class models.
- **Large context mode automation**: Adjusted the logic so that Large Context Mode turns on immediately when token usage exceeds 200,000 tokens (tiktoken basis), without waiting for an explicit provider limit error.

**Detailed Implementation**

- **Model configuration and testing**: Updated `claude-sonnet-4.5` metadata, gateway mappings, and test cases so the new model works across the entire pipeline.
- **Proactive thresholding**: For SoTA models like claude-sonnet-4.5 and gemini-2.5-pro that incur extra costs beyond 200k tokens, Large Context Mode now kicks in as soon as usage passes the 200k mark.

## [0.1.9] - 2025-09-26

### Added

#### MCP (Model Context Protocol) Server Implementation

**Core Changes**

- **MCP Server Support**: Selvage now supports MCP server mode, enabling direct access to code review features from Claude Code, Cursor, and other MCP clients.

  - **Server Mode**: Launch with `selvage mcp` command
  - **Full Feature Access**: All existing review and utility features available

**Implementation Details**

- **Server Architecture**: FastMCP-based implementation (`selvage/src/mcp/server.py`)
- **Response Models**: Pydantic-based structured models (`selvage/src/mcp/models/`)
- **Protocol Integration**: Existing features exposed via MCP protocol
- **CLI Integration**: Added `selvage mcp` command with stderr handling

## [0.1.8] - 2025-09-15

### Added

#### feat: Enhanced Internationalization Support and User Experience Improvements

**Core Changes**

- **Comprehensive English Message Unification**: Unified all user-facing text including CLI messages, error messages, and model descriptions to English, improving accessibility for international users
- **Default Language Setting Change**: Changed system default language from Korean to English to create a more globally user-friendly environment
- **README Documentation Improvements**: Updated demo videos and visual materials to enhance user understanding

**Detailed Implementation**

- **CLI Message Localization**: Converted all command outputs, warnings, and error messages to English
- **Model Information Internationalization**: Unified model descriptions for OpenAI, Anthropic, Google, and OpenRouter to English
- **Test Stability Enhancement**: Added Docker automatic pull and retry logic to Python version compatibility tests
- **API Key Management Improvements**: Added API key verification functionality and localized related messages to English
- **Exception Handling Message Improvements**: Localized JSON parsing, Git diff, and context limit related error messages to English

## [0.1.7] - 2025-08-24

### Added

#### feat: OpenRouter First Approach and API Stability Improvements

**Core Changes**

- **OpenRouter First Usage Approach**: Transitioned to OpenRouter First approach enabling access to all AI models with a single API key
- **New GPT-5 Model Support**: Added gpt-5, gpt-5-high, gpt-5-mini models providing advanced reasoning and diverse performance options
- **Enhanced API Response Handling**: Added ChatCompletion to LLMResponse type and supported various response formats
- **Environment Variable Priority Setting**: Simplified configuration approach by removing CLI flags and using environment variables exclusively

**Detailed Implementation**

- **JSON Parsing Error Handling**: Refactored JSONParsingError class and added response text truncation functionality
- **Enhanced Retry Logic**: Improved tenacity-based retry mechanism and exception handling approach
- **Expanded Error Patterns**: Added OpenAI, Anthropic context limit and OpenRouter related error patterns
- **Improved API Key Validation**: Enhanced environment variable-based configuration validation logic and user guidance messages

## [0.1.6] - 2025-08-15

### Added

#### feat: Multi-turn Review System Implementation

**Core Changes**

- **Automatic Context Limit Handling**: Implemented multi-turn review system that automatically splits prompts when LLM API context limits are exceeded, processes them sequentially, and intelligently synthesizes results
- **Intelligent Prompt Splitting**: Optimal splitting based on greedy algorithm considering token information and text length (securing 20% safety margin)
- **LLM-based Result Synthesis**: Intelligent synthesis using LLM for Summary, with fallback logic applied on failure

**Detailed Implementation**

- **MultiturnReviewExecutor**: Main coordinator for multi-turn review process
- **PromptSplitter**: Token ratio calculation and text length-based equal distribution algorithm
- **ReviewSynthesizer**: Intelligent result synthesis through simple Issues aggregation, Summary LLM synthesis, and Recommendations deduplication
- **SynthesisAPIClient & SynthesisPromptManager**: Unified API calls supporting all LLM providers and task-specific prompt management

**Performance Optimization and Stability**

- **Sequential Processing Approach**: Transitioned from parallel to sequential processing to resolve OpenRouter concurrency issues
- **Accurate Cost Calculation**: Transparent calculation and display of total chunk processing costs and synthesis costs
- **Improved Error Patterns**: Added new Anthropic context limit error patterns, increased max_tokens value to 64000

**Documentation and Development Guide**

- **Detailed System Documentation**: Added `.cursor/rules/multiturn-review-system.mdc` for comprehensive documentation of component dependencies, workflows, splitting strategies, etc.
- **Architecture Integration**: Integrated multi-turn processing steps into existing workflow documentation to improve overall system understanding

## [0.1.5] - 2025-08-06

### Added

#### feat: Code Review System Improvements and Performance Optimization

**Core Changes**

- **Line Number Calculation Optimization**: Transferred target_code line_number calculation responsibility from LLM to Python code, improving accuracy
- **System Prompt v4 Introduction**: Enhanced summary field guidelines and improved code quality evaluation criteria
- **File Reading Performance Optimization**: Implemented cache system for significant performance improvements when repeatedly accessing the same file

**Detailed Improvements**

- **FormattedHunk Class Optimization**: Reduced memory usage by removing unnecessary attributes
- **Enhanced Testing**: Added comprehensive test cases with 325 lines for line number calculator
- **Improved API Key Error Handling**: Added verification for various error scenarios and segfault prevention logic

## [0.1.4] - 2025-08-03

### Added

#### feat: Context Extract Feature Implementation

**Core Features**

##### Context Extraction Improvements

- **Tree-sitter Based Smart Context Extractor**: Introduced AST analysis to automatically extract the smallest code blocks containing changed lines and dependency statements (import, require, define, etc.) present in files
  - **Multi-language Support**: Professional context extraction support for Python, JavaScript/TypeScript, Java/Kotlin languages
  - **Smart Context Application Conditions**: Used when changed lines are 20% or less of the total file, otherwise uses full file context
- **Fallback Context Extractor**: For unsupported languages (C, C#, Go, Swift, etc.), extracts context using regex-based pattern matching

**Additional Improvements**

- **System Prompt Improvements**: Upgraded system prompts to provide more accurate context-based code reviews
- **Meaningless Change Filtering**: Automatically filters out meaningless changes such as empty lines, comments, preprocessor directives, etc., to improve review quality
