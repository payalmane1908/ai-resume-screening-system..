# Contributing to AI Resume Screening System

Thank you for your interest in contributing! Here's how to get started.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```
4. **Copy** `.env.example` to `.env` and fill in your values
5. **Run** the app: `python app.py`

## Development Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Write meaningful commit messages using [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat: add PDF parsing support`
  - `fix: handle empty CSV rows`
  - `docs: update API documentation`
- Add tests for new features in the `tests/` directory
- Run tests before submitting: `python -m pytest tests/ -v`

## Pull Request Process

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes and commit
3. Push to your fork and open a Pull Request
4. Describe what your PR does and link any related issues

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Python version and OS

## Code of Conduct

Be respectful and constructive. We're all here to learn and build together.
