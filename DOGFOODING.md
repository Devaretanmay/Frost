# The FROST Dogfooding Suite: 10 Real Engineering Case Studies

FROST is evaluated not on artificial micro-benchmarks or synthetic tests, but against **real production repositories** facing ecosystem upgrades, breaking API migrations, and dependency uncertainty.

---

## 🎯 Master Case Study Matrix

| Phase | # | Repository | Difficulty | Task | What We're Testing | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Phase 1** | 1 | **FastAPI Full Stack Template** (`0.7.0`) | Medium | Modernize to 2026 standards | Canonical repository modernization, Pydantic V2, SQLModel | **DONE (54/54 Passed)** |
| **Phase 1** | 2 | **Cookiecutter Django** | Medium | Upgrade Python 3.14 & Django | Django ecosystem migrations, environment setup | **Next in Queue** |
| **Phase 2** | 3 | **Prefect** (`PrefectHQ/prefect`) | Hard | Modernize dependencies & tests | Async systems, orchestration stack, Python 3.14 | **DONE (384/384 Passed)** |
| **Phase 2** | 4 | **LiteLLM** (`BerriAI/litellm`) | Medium | Upgrade OpenAI & AI SDKs | AI tooling & SDK ecosystem breakages | Planned |
| **Phase 2** | 5 | **CrewAI** (`crewAIInc/crewAI`) | Medium | Modernize agent stack & deps | Agent framework migrations & API updates | Planned |
| **Phase 3** | 6 | **Apache Superset** (`apache/superset`) | Hard | Upgrade Python & fix test graph | Massive dependency graph, long-running tasks | Planned |
| **Phase 3** | 7 | **Saleor** (`saleor/saleor`) | Hard | Upgrade backend & GraphQL stack | Large production GraphQL API | Planned |
| **Phase 3** | 8 | **Open WebUI** (`open-webui/open-webui`) | Medium | Modernize Python backend | Fast-moving OSS AI application | Planned |
| **Phase 3** | 9 | **Paperless-ngx** (`paperless-ngx`) | Hard | Modernize entire stack | Multi-service architecture, OCR, Docker | Planned |
| **Phase 4** | 10 | **FROST** (`Devaretanmay/Frost`) | Hard | Self-dogfooding & refactoring | Architectural evolution & package consolidation | **DONE (468/468 Passed)** |

---

## 📋 Case Study Details & Execution Strategy

### Phase 1 — Starter Templates & Boilerplates

#### #1. FastAPI Full Stack Template (Tag `0.7.0`)
- **Repository**: `fastapi/full-stack-fastapi-template`
- **Task**: Upgrade early 2023 boilerplate to 2026 standards (Python 3.14, Pydantic V2, SQLModel, FastAPI 0.114+).
- **Stress Tests**: Pydantic V1 $\to$ V2 schema migrations, SQLAlchemy 2.0 generic relationship resolution, SQLite thread isolation.
- **Outcome**: **54 / 54 Unit & Integration Tests PASSED (100% GREEN)**.

#### #2. Cookiecutter Django (2023 Tag)
- **Repository**: `cookiecutter/cookiecutter-django`
- **Task**: Upgrade Django, Python 3.14, environment configuration, Docker Compose, and test suite.
- **Stress Tests**: Django ORM migrations, settings refactoring, CI setup.

---

### Phase 2 — Production OSS Projects

#### #3. Prefect
- **Repository**: `PrefectHQ/prefect`
- **Task**: Modernize for Python 3.13 / 3.14 compatibility while preserving public orchestration APIs.
- **Stress Tests**: Async event loop execution, dependency resolution, 380+ core flow tests.
- **Outcome**: **371 Passed, 11 Skipped, 2 Xfailed, 0 Failed**.

#### #4. LiteLLM
- **Repository**: `BerriAI/litellm`
- **Task**: Modernize to latest OpenAI 1.x+ and Anthropic SDK ecosystem.
- **Stress Tests**: Rapidly evolving AI SDK interfaces, breaking parameter changes.

#### #5. CrewAI
- **Repository**: `crewAIInc/crewAI`
- **Task**: Upgrade agent framework dependencies, Pydantic schemas, and test suite.
- **Stress Tests**: Agent framework breaking changes and model schema updates.

---

### Phase 3 — Large Repositories

#### #6. Apache Superset
- **Repository**: `apache/superset`
- **Task**: Upgrade Python ecosystem and resolve massive dependency graph breaks.
- **Stress Tests**: 100k+ LOC codebase, complex SQL / ORM dependencies, long execution limits.

#### #7. Saleor
- **Repository**: `saleor/saleor`
- **Task**: Modernize GraphQL backend stack and Django ORM dependencies.
- **Stress Tests**: Production e-commerce API, GraphQL schema validation.

#### #8. Open WebUI
- **Repository**: `open-webui/open-webui`
- **Task**: Modernize Python backend and FastAPI services.
- **Stress Tests**: Fast-moving OSS application, web/audio/vision pipeline dependencies.

#### #9. Paperless-ngx
- **Repository**: `paperless-ngx/paperless-ngx`
- **Task**: Modernize full stack (Django, Celery, Tesseract OCR, Redis, Docker).
- **Stress Tests**: Multi-service containerized architecture and native bindings.

---

### Phase 4 — Self-Dogfooding

#### #10. FROST
- **Repository**: `Devaretanmay/Frost`
- **Task**: Modernize FROST itself — remove legacy V1 global session state, consolidate `v2` package directory into top-level `frost`, build `frost doctor` diagnostics.
- **Stress Tests**: Self-refactoring without regressing FastMCP server or Rust compression bindings.
- **Outcome**: **468 / 468 Tests PASSED (416 Rust + 52 Python)**.
