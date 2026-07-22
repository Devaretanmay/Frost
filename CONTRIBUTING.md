# Contributing to FROST

Thank you for your interest in contributing to FROST! We welcome contributions from the community.

## Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Devaretanmay/Frost.git
   cd Frost
   ```

2. **Create a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install maturin pytest mcp
   ```

3. **Build Rust Bindings**:
   ```bash
   maturin develop --offline
   ```

## Running Tests

Before submitting a pull request, ensure all Python and Rust tests pass:

```bash
# Run Python integration tests
pytest tests/

# Run Rust core tests
cargo test
```

## Architectural Guidelines

When contributing to FROST, adhere to the 7 Architectural Invariants:
1. **Linear execution is default**.
2. **Branch only at uncertainty points**.
3. **Branches are tiny and short-lived**.
4. **Compress before reasoning**.
5. **Detect internal loops**.
6. **Kill bad branches aggressively**.
7. **Merge immediately after a winner is selected**.

## Submitting Pull Requests

1. Create a feature branch (`git checkout -b feature/my-feature`).
2. Commit your changes with clear, descriptive commit messages.
3. Verify tests and linting pass locally.
4. Push to your branch and open a Pull Request.

## License

By contributing to FROST, you agree that your contributions will be licensed under the repo's [MIT License](LICENSE).
