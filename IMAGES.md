# FROST Images

FROST executes tasks inside Docker containers. The Docker image determines what tools are available. By default, FROST uses `python:3.12` — a general-purpose image with Python and common system tools, but **no language-specific tools** like pytest, cargo, or node.

Set the image with `FROST_IMAGE` or pass `image=` to `frost()`:

```bash
export FROST_IMAGE="my-custom-image:latest"
```

```python
result = frost("pytest tests/", image="python:3.12-slim")
```

---

## Quick Reference

| Use case | Image | Size | Tools |
|----------|-------|------|-------|
| Minimal Python | `python:3.12-slim` | ~100 MB | Python stdlib only |
| General Python | `python:3.12` | ~1 GB | Python + system build tools |
| Python + pytest | `frost-py` (build below) | ~1 GB | Python + pytest + common libs |
| Rust | `rust:latest` | ~1.5 GB | cargo, rustc, rustup |
| Node.js | `node:22` | ~350 MB | node, npm, npx |
| Full dev | `frost-dev` (build below) | ~2 GB | Python + Rust + Node + git |
| Go | `golang:latest` | ~800 MB | go, go build |
| Java | `eclipse-temurin:21` | ~400 MB | java, javac, maven/gradle |
| .NET | `mcr.microsoft.com/dotnet/sdk:9.0` | ~800 MB | dotnet |
| Custom | Your own Dockerfile | Varies | Whatever you need |

---

## Python

### Minimal: `python:3.12-slim` (~100 MB)

Python stdlib only. No pip cache, no build tools. Good for simple scripts that don't import third-party packages.

```python
frost("python3 -c \"print('hello')\"", image="python:3.12-slim")
```

**Limitation:** No pytest, no requests, no numpy, nothing beyond stdlib.

### General: `python:3.12` (~1 GB)

Full Python with build tools. Can `pip install` packages at runtime, but install time adds to each FROST session.

```python
frost("pip install pytest && pytest tests/", image="python:3.12")
```

### Pre-built: Build a custom Python image with tools installed

Create a `Dockerfile.frost-py`:

```dockerfile
FROM python:3.12

RUN pip install --no-cache-dir pytest pytest-cov mypy ruff black
RUN mkdir /workspace
WORKDIR /workspace
```

Build and use:

```bash
docker build -t frost-py -f Dockerfile.frost-py .
```

```python
frost("pytest tests/", image="frost-py")
```

---

## Rust

### `rust:latest` (~1.5 GB)

Full Rust toolchain. Use for compiling and testing Rust projects.

```python
frost("cargo test", image="rust:latest")
```

**Note:** `rust:latest` is based on Debian and includes system build tools (gcc, make, etc.). It's the official Rust image.

### Smaller: `rust:slim-bookworm` (~600 MB)

If you don't need the full toolchain:

```python
frost("cargo build --release", image="rust:slim-bookworm")
```

---

## Node.js

### `node:22` (~350 MB)

Full Node.js with npm. Use for JavaScript/TypeScript projects.

```python
frost("npm test", image="node:22")
frost("npx jest --coverage", image="node:22")
```

### `node:22-alpine` (~120 MB)

Smaller image if you don't need native build tools:

```python
frost("node script.js", image="node:22-alpine")
```

---

## Full Development Image

For agents that switch between languages, build a combined image:

`Dockerfile.frost-dev`:

```dockerfile
FROM python:3.12

# Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Node
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Python tools
RUN pip install --no-cache-dir pytest pytest-cov mypy ruff

# Git
RUN apt-get install -y git

WORKDIR /workspace
```

Build and use:

```bash
docker build -t frost-dev -f Dockerfile.frost-dev .
```

```python
frost("pytest tests/ && cargo test", image="frost-dev")
```

---

## Passing the Image

| Method | Example |
|--------|---------|
| Environment variable | `export FROST_IMAGE="rust:latest"` |
| `frost()` parameter | `frost("cargo test", image="rust:latest")` |
| MCP tool argument | `frost("cargo test", image="rust:latest")` |

The image is resolved in this order:

1. `image=` parameter passed to `frost()`
2. `FROST_IMAGE` environment variable
3. Default: `python:3.12`

---

## Tips

### Speed up first-run

Docker pulls images on first use. Pre-pull frequently used images:

```bash
docker pull python:3.12
docker pull rust:latest
docker pull node:22
```

### Avoid `-alpine` for complex tools

Alpine uses musl libc instead of glibc. Many Python packages (numpy, pandas, psycopg2) and Rust projects require glibc. Use `-slim` variants (Debian-based) instead of `-alpine` unless you know musl works for your use case.

### Persist dependencies

If you `pip install` or `npm install` inside a FROST session, the packages are gone when the container stops. For repeated use, build a custom image with dependencies pre-installed.

### Check what's in the image

If a command fails with "not found," check what's available:

```python
result = frost("which python3 && which node && which cargo")
```
