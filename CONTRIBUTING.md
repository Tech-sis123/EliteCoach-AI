# Contributing to Elite Coach AI

Welcome to the team! We maintain high standards for code quality, testing, and documentation. This guide outlines how to contribute effectively to the backend.

## 🛠 Development Workflow

### 1. Environment Setup
- **Python**: Version 3.13+ required.
- **Windows Users**: Must install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) to support async database drivers.
- **Installation**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
  pip install -r requirements.txt
  ```

### 2. Branching Strategy
We use a feature-branch workflow.
- `main`: Production-ready code.
- `develop`: Pre-production integration branch.
- `feature/*`: New features.
- `fix/*`: Bug fixes.
- `refactor/*`: Code improvements without functional changes.

### 2. Coding Standards
- **PEP 8**: All Python code must strictly follow PEP 8 standards. We use `black` for formatting and `isort` for import organization.
- **Type Hinting**: All function signatures **must** include type hints (Python 3.12+ features preferred).
- **Docstrings**: Use Google-style docstrings for all services and API endpoints.

### 3. Testing Requirements
We take a **Test-Driven Development (TDD)** approach.
- **Coverage**: New features must have at least 90% test coverage.
- **Execution**: Run the full suite before opening a PR:
  ```bash
  pytest tests/ -n auto
  ```
- **Structure**: Tests must be independent and use the `fixture` system defined in `tests/conftest.py`.

## 📝 Pull Request (PR) Process
1. **Description**: Clearly explain *what* changed and *why*.
2. **Issue Linking**: Use "Closes #123" to link relevant Jira/GitHub issues.
3. **Peer Review**: At least one senior developer must approve the PR.
4. **CI/CD**: All PRs must pass the automated GitHub Actions pipeline (Linting, Testing, Security Audit).

## 🔒 Security Best Practices
- Never commit `.env` files or hardcoded credentials.
- Use `SECRET_KEY` from environment variables only.
- Ensure all new endpoints use the `get_current_user` dependency for authentication unless explicitly public.

---

*Thank you for helping us democratize professional coaching with AI!*
