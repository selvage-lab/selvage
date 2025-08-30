<h1 align="center">Selvage: AI-Powered Code Review Automation Tool</h1>

<p align="center">🌐 <a href="README.md"><strong>한국어</strong></a></p>

<p align="center"><strong>A modern CLI tool that helps AI analyze Git diffs to improve code quality, find bugs, and identify security vulnerabilities.</strong></p>

<p align="center">
  <a href="https://pypi.org/project/selvage/"><img alt="PyPI" src="https://img.shields.io/pypi/v/selvage"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10+-blue">
  <img alt="AI Models" src="https://img.shields.io/badge/AI-GPT--5%20%7C%20Claude%20%7C%20Gemini-green">
</p>

<!-- TODO: Add demo GIF -->
<!-- <p align="center"> <img src="[Demo GIF URL]" width="100%" alt="Selvage Demo"/> </p> -->

<p align="center">
  <img src="assets/demo.gif" width="100%" alt="Selvage Demo"/>
</p>

**Selvage: Code reviews with an edge!**

No more waiting for reviews! AI instantly analyzes your code changes to provide quality improvements and bug prevention.  
With smart context analysis (AST-based) that's accurate and cost-effective, plus multi-turn processing for large codebases - seamlessly integrated with all Git workflows.

<details>
<summary><strong>Table of Contents</strong></summary>

- [✨ Key Features](#-key-features)
- [🚀 Quick Start](#-quick-start)
- [🌐 Smart Context Analysis and Supported AI Models](#-smart-context-analysis-and-supported-ai-models)
  - [Smart Context Analysis](#-smart-context-analysis)
  - [Supported AI Models](#supported-ai-models)
- [⌨️ CLI Usage](#️-cli-usage)
  - [Configuring Selvage](#configuring-selvage)
  - [Code Review](#code-review)
  - [Viewing Results](#viewing-results)
- [📄 Review Result Storage Format](#-review-result-storage-format)
- [🛠️ Advanced Usage](#️-advanced-usage)
  - [Troubleshooting](#troubleshooting)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)
- [📞 Contact and Community](#-contact-and-community)

</details>

## ✨ Key Features

- **🤖 Multiple AI Model Support**: Leverage the latest LLM models including OpenAI GPT-5, Anthropic Claude Sonnet-4, Google Gemini, and more
- **🔍 Git Workflow Integration**: Support for analyzing staged, unstaged, and specific commit/branch changes
- **🐛 Comprehensive Code Review**: Bug and logic error detection, code quality and readability improvement suggestions
- **🎯 Optimized Context Analysis**: Automatic extraction of the smallest code blocks and dependency statements containing changed lines through Tree-sitter based AST analysis, providing contextually optimized information
- **🔄 Automatic Multi-turn Processing**: Automatic prompt splitting when context limits are exceeded, supporting stable large-scale code reviews
- **📖 Open Source**: Freely use and modify under Apache-2.0 License

## 🚀 Quick Start

### 1. Installation

```bash
pip install selvage
```

### 2. API Key Setup

Get an API key from [OpenRouter](https://openrouter.ai) and set it up:

```bash
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

### 3. Start Code Review

```bash
selvage review --model claude-sonnet-4-thinking
```

🎉 **Done!** Review results will be output directly to your terminal.

**💡 More Options:** [CLI Usage](#️-cli-usage) | [Advanced Usage](#️-advanced-usage)

---

## ⌨️ CLI Usage

### Configuring Selvage

```bash
# View all settings
selvage config list

# Set default model
selvage config model <model_name>

# Set default language
selvage config language <language_name>

```

### Code Review

```bash
selvage review [OPTIONS]
```

#### Key Options

- `--repo-path <path>`: Git repository path (default: current directory)
- `--staged`: Review only staged changes
- `--target-commit <commit_id>`: Review changes from specific commit to HEAD (e.g., abc1234)
- `--target-branch <branch_name>`: Review changes between current branch and specified branch (e.g., main)
- `--model <model_name>`: AI model to use (e.g., claude-sonnet-4-thinking)
- `--open-ui`: Automatically launch UI after review completion
- `--no-print`: Don't output review results to terminal (terminal output enabled by default)
- `--skip-cache`: Perform new review without using cache

#### Usage Examples

```bash
# Review current working directory changes
selvage review

# Final check before commit
selvage review --staged

# Review specific files only
git add specific_files.py && selvage review --staged

# Code review before sending PR
selvage review --target-branch develop

# Quick and economical review for simple changes
selvage review --model gemini-2.5-flash

# Review and then view detailed results in web UI
selvage review --target-branch main --open-ui
```

### Viewing Results

Review results are **output directly to the terminal** and automatically saved to files simultaneously.

For **additional review management and re-examination**, you can use the web UI:

```bash
# Manage all saved review results in web UI
selvage view

# Run UI on different port
selvage view --port 8502
```

**Key UI Features:**

- 📋 Display list of all review results
- 🎨 Markdown format display
- 🗂️ JSON structured result view

## 🌐 Smart Context Analysis and Supported AI Models

### 🎯 Smart Context Analysis

Selvage uses **Tree-sitter based AST analysis** to precisely extract only the code blocks related to changed lines, **ensuring both cost efficiency and review quality simultaneously**.

#### How Smart Context Works

- **Precise Extraction**: Extracts only the minimal function/class blocks containing changed lines + related dependencies (imports, etc.)
- **Cost Optimization**: Dramatically reduces token usage by sending only necessary context instead of entire files
- **Quality Assurance**: Maintains high review accuracy through AST-based precise code structure understanding

#### Smart Context Automatic Application

Selvage analyzes file size and change scope to **automatically select the most efficient review method**:

```
🎯 Small Changes           → Fast and accurate analysis with Smart Context
📄 Small Files            → Complete context understanding with full file analysis
📋 Partial Edits in Large Files → Focused analysis of related code with Smart Context
📚 Large Changes in Big Files   → Comprehensive review with full file analysis
```

> 💡 **Automatic Optimization**: The optimal analysis method for each situation is automatically applied without any manual configuration.

#### Supported Languages (AST-based)

- **Python**, **JavaScript**, **TypeScript**, **Java**, **Kotlin**

#### Full Language Support

- **All Programming Languages**: Go, Ruby, PHP, C#, C/C++, Rust, Swift, Dart, etc.
- **Markup & Configuration Files**: HTML, CSS, Markdown, JSON, YAML, XML, etc.
- **Scripts & Others**: Shell, SQL, Dockerfile, other text-based files

> 🚀 **Universal context extraction method** provides **excellent code review quality** for all languages.  
> AST-based supported languages are continuously expanding.

---

### Supported AI Models

🚀 **Manage all models below with just one OpenRouter API key!**

#### OpenAI Models (OpenRouter or OpenAI API Key)

- **gpt-5**: Latest advanced reasoning model (400K context)
- **gpt-5-high**: ⭐ **Recommended** - High accuracy reasoning model (400K context)
- **gpt-5-mini**: Lightweight fast response model (400K context)

#### Anthropic Models (OpenRouter or Anthropic API Key)

- **claude-sonnet-4**: Hybrid reasoning model optimized for advanced coding (200K context)
- **claude-sonnet-4-thinking**: ⭐ **Recommended** - Extended thinking process support (200K context)

#### Google Models (OpenRouter or Google API Key)

- **gemini-2.5-pro**: Large context and advanced reasoning (1M+ tokens)
- **gemini-2.5-flash**: Response speed and cost efficiency optimized (1M+ tokens)

#### 🌟 OpenRouter Provided Models (OpenRouter API Key Only)

- **qwen3-coder** (Qwen): ⭐ **Recommended** - 480B parameter MoE coding-specialized model (1M+ tokens)
- **kimi-k2** (Moonshot AI): 1T parameter MoE large-scale reasoning model (128K tokens)

## 📄 Review Result Storage Format

Review results are saved as **structured files** simultaneously with terminal output:

- **📋 Markdown Format**: Clean structure that's easy for humans to read, including summary, issue list, and improvement suggestions
- **🔧 JSON Format**: For programmatic processing and integration with other tools

<p align="center">
  <img src="assets/demo-ui.png" width="100%" alt="Selvage UI Demo"/>
</p>

## 🛠️ Advanced Usage

### Various Git Workflow Integration

#### Team Collaboration Workflows

```bash
# Code quality verification before Pull Request creation
selvage review --target-branch main --model claude-sonnet-4-thinking

# Pre-analysis of changes for code reviewers
selvage review --target-branch develop --model claude-sonnet-4-thinking

# Comprehensive review of all changes after specific commit
selvage review --target-commit a1b2c3d --model claude-sonnet-4-thinking
```

#### Development Stage Quality Management

```bash
# Quick feedback during development (before WIP commit)
selvage review --model gemini-2.5-flash

# Final verification of staged changes (before commit)
selvage review --staged --model claude-sonnet-4-thinking

# Emergency review before hotfix deployment
selvage review --target-branch main --model claude-sonnet-4-thinking
```

### Large-scale Code Review

```bash
# Large codebases are automatically handled
selvage review --model claude-sonnet-4  # Usage is the same, multi-turn processing automatically applied after detection
```

Selvage automatically handles large code changes that exceed LLM model context limits.  
Long Context Mode runs automatically, so just wait for it to complete.

### Cost Optimization

```bash
# Use economical models for small changes
selvage review --model gemini-2.5-flash
```

### Troubleshooting

#### Common Errors

**API Key Error**

```bash
# Check environment variable
echo $OPENROUTER_API_KEY

# Permanent setup (Linux/macOS)
echo 'export OPENROUTER_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Model not found Error**

```bash
# Check available model list
selvage models

# Use correct model name
selvage review --model claude-sonnet-4-thinking
```

**Network Connection Error**

```bash
# Retry ignoring cache
selvage review --skip-cache

# Check detailed info with debug mode
selvage config debug-mode on
selvage review
```

## 💡 Advanced Settings (For Developers/Contributors)

<details>
<summary><strong>Development and Advanced Settings Options</strong></summary>

### Development Version Installation

```bash
git clone https://github.com/selvage-lab/selvage.git
cd selvage
pip install -e .
```

### Development Environment Installation

```bash
# Install with development dependencies (pytest, build, etc.)
pip install -e .[dev]

# Install with development + E2E test environment (testcontainers, docker, etc.)
pip install -e .[dev,e2e]
```

### Individual Provider API Key Usage

You can also set individual provider API keys instead of OpenRouter:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### Development and Debugging Settings

```bash
# Set default model to use (for advanced users)
selvage config model claude-sonnet-4-thinking

# Check configuration
selvage config list

# Enable debug mode (for troubleshooting and development)
selvage config debug-mode on
```

</details>

## 🤝 Contributing

Selvage is an open-source project and we always welcome your contributions! Bug reports, feature suggestions, documentation improvements, code contributions - any form of contribution is appreciated.

**How to Contribute:**

- 🐛 Bug reports or feature suggestions on [GitHub Issues](https://github.com/selvage-lab/selvage/issues)
- 🔧 Code contributions through Pull Requests
- 📚 Documentation improvements and translations

**Detailed contribution guidelines can be found in [CONTRIBUTING.md](CONTRIBUTING.md).**

## 📜 License

Selvage is distributed under the [Apache License 2.0](LICENSE). This license permits commercial use, modification, and distribution, with comprehensive patent protection and trademark restrictions included.

## 📞 Contact and Community

- **🐛 Bug Reports and Feature Requests**: [GitHub Issues](https://github.com/selvage-lab/selvage/issues)
- **📧 Direct Contact**: contact@selvage.me

---

<p align="center">
  <strong>Write better code with Selvage! 🚀</strong><br>
  ⭐ If this project helped you, please give us a Star on GitHub!
</p>
