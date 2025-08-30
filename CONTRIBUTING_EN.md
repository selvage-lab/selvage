# Contributing Guide (Contributing to Selvage)

<p align="center">🌐 <a href="CONTRIBUTING.md"><strong>한국어</strong></a></p>

Thank you for your interest in contributing to Selvage! We value community participation and welcome your help in creating a better AI-powered code review tool.

This document provides guidelines on how to contribute to Selvage. Taking a moment to read this before contributing will help ensure smooth collaboration.

## 🤝 How to Contribute

We welcome various forms of contributions. Selvage is a completely open-source project under the Apache-2.0 license, encouraging free participation and contributions from the community.

### 🐛 Bug Reports

If you discover a bug, please report it anytime through [GitHub Issues](https://github.com/anomie7/selvage/issues).

**Information to include when creating an issue:**

- **Environment Information**: Operating system, Python version, Selvage version
- **Commands Used**: The selvage commands and options you executed
- **AI Model Used**: Which model you used (e.g., claude-sonnet-4-thinking)
- **Reproduction Steps**: Step-by-step description to reproduce the bug
- **Expected vs Actual Results**: What you expected and what actually happened
- **Logs and Error Messages**: Related error messages or logs (if available)
- **Git Diff Sample**: Code changes where the issue occurred (within non-sensitive scope)

### ✨ Feature Requests

If you have ideas for new features or improvements, please suggest them through [GitHub Issues](https://github.com/anomie7/selvage/issues).

**Information to include in proposals:**

- **Feature Description**: Clear description of the proposed feature
- **Use Cases**: Situations where this feature would be useful
- **Expected Benefits**: Improvements this feature would bring
- **Alternative Review**: Content reviewing whether existing features can solve the problem

### 🛠️ Code Contributions

#### Welcome Types of Contributions:

- **Bug Fixes**: Resolving discovered bugs
- **Feature Improvements**: Enhancing performance and usability of existing features
- **New Features**: New features requested by the community
- **Adding Tests**: Improving test coverage
- **Refactoring**: Improving code quality and structure
- **Expanding AI Model Support**: Adding new LLM models or providers

#### Good Issues to Start With:

Check for issues labeled `good first issue`, `help wanted`, or `bug`.

### 📚 Documentation Improvements

Documentation contributions are always welcome:

- **README Improvements**: Adding usage examples and guides
- **API Documentation**: Improving code comments and docstrings
- **Tutorials**: Creating use case-specific guides
- **Translations**: Supporting multilingual documentation
- **Typo Fixes**: Correcting spelling and grammar errors

## 📝 Pull Request (PR) Process

### 1. Development Environment Setup

```bash
# Fork the repository and clone
git clone https://github.com/YOUR_USERNAME/selvage.git
cd selvage

# Install development environment
pip install -e .[dev,e2e]

# Run tests to verify environment
pytest tests/
```

### 2. Branch Creation and Development

```bash
# Create new branch
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-number

# Write and modify code
# ... development work ...

# Run tests
pytest tests/

# Code style check (using Ruff)
ruff check .
ruff format .
```

### 3. Commit and Push

All commits must include a Signed-off-by line according to the [Developer Certificate of Origin (DCO)](DCO).

```bash
# Set up DCO template (one-time setup)
git config commit.template .gitmessage

# Commit with meaningful message (-s flag required)
git add .
git commit -s -m "feat: add new feature for XYZ"

# Push branch
git push origin feat/your-feature-name
```

**Important**: The `-s` flag automatically adds a `Signed-off-by: Your Name <your.email@example.com>` line to your commit. This certifies that you have the right to make this contribution.

### 4. Creating Pull Requests

When creating a Pull Request on GitHub:

**PR Title Guidelines:**

- `feat: add new feature`
- `fix: resolve bug`
- `docs: improve documentation`
- `test: add/modify tests`
- `refactor: refactor code`

**Content to include in PR description:**

- Summary of changes
- Related issue numbers (e.g., `Closes #123`)
- Testing methods and results
- Screenshots (for UI changes)
- Checklist (using template below)

**PR Checklist:**

```markdown
- [ ] All commits comply with DCO and include Signed-off-by lines
- [ ] Tests added or existing tests pass
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if necessary)
- [ ] Changes do not break existing functionality
```

## ✅ Code Review

### Review Criteria:

- **Functionality**: Does it work as intended?
- **Code Quality**: Is it readable and maintainable?
- **Testing**: Are appropriate tests included?
- **Documentation**: Are necessary documents updated?
- **Compatibility**: Does it not break existing functionality?

### Review Process:

1. Verify automated tests pass
2. Verify code style checks (Ruff) pass
3. Management team code review
4. Request modifications and re-review if needed
5. Merge after approval

## 🔧 Development Guidelines

### Code Style

Selvage follows these coding styles:

- **Formatter**: Use Ruff format
- **Linter**: Use Ruff lint
- **Type Hints**: Apply type hints to all functions
- **Docstring**: Use Google-style docstrings

### Writing Tests

- **Unit Tests**: Unit tests for new functions/classes
- **E2E Tests**: End-to-end tests for complete workflows

### Commit Message Guidelines

#### Recommended Format for Selvage Project:

```
<type>: <subject> (50 characters or less)

# Body: Explain what and why (optional)
# - What was changed
# - Why the change was necessary
# - Impact of the change

# Footer (optional):
# Fixes: #123
# Closes: #456
# Refs: #789
```

**Examples:**

```
feat: add Claude Sonnet-4 model support

- Add Anthropic Claude Sonnet-4 model to supported model list
- Implement model configuration and API call logic
- Write related test cases

Fixes: #42
```

**Type Categories:**

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (no functionality changes)
- `refactor`: Refactoring
- `test`: Adding/modifying tests
- `chore`: Build process, tool setup, etc.

## 🌟 Open Source Spirit

Selvage is a completely open-source project under the Apache-2.0 license. We pursue the following values:

- **Transparency**: All development processes are open and transparent
- **Inclusivity**: We welcome contributors from all backgrounds
- **Collaboration**: We build better tools together with the community
- **Quality**: We pursue high code quality and user experience

## 📞 Communication Channels

- **Issues and Discussions**: [GitHub Issues](https://github.com/anomie7/selvage/issues)
- **Direct Contact**: anomie7777@gmail.com
- **Code Contributions**: Contributions through Pull Requests

## 📜 Code of Conduct

All participants are asked to participate in the spirit of mutual respect and inclusion:

- Respect and consider other participants
- Provide constructive feedback
- Acknowledge diverse perspectives and experiences
- Focus on project goals

---

**Thank you for contributing to Selvage! 🚀**

Your contributions help improve the code review experience for developers worldwide.