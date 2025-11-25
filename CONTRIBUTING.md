# Contributing to SOMA

Thank you for your interest in SOMA (State-Oriented Machine Algebra)!

## Project Status

SOMA is a research project exploring state-oriented computational models. Development is primarily driven by research goals and experimentation.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear, descriptive title
- Steps to reproduce the behavior
- Expected vs actual behavior
- SOMA version and environment details

### Suggesting Features

Feature requests are welcome! Please open an issue describing:
- The use case or problem you're trying to solve
- How the feature would work
- Why it fits SOMA's design philosophy (explicit state, no hidden semantics)

### Pull Requests

Pull requests are welcome, especially for:
- Bug fixes
- Documentation improvements
- Test coverage
- Example programs

Before submitting a large PR, consider opening an issue first to discuss the approach.

**PR Guidelines:**
- All tests must pass (`python3 tests/run_soma_tests.py`)
- Add tests for new functionality
- Update documentation as needed
- Follow existing code style

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/soma.git
cd soma

# Run tests
python3 tests/run_soma_tests.py

# Run Python unit tests
python3 -m pytest tests/test_*.py -v
```

## Questions?

Open an issue for questions about SOMA's design, implementation, or usage.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
