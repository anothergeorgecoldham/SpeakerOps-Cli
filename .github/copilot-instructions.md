# Copilot instructions for SpeakerOps

## Build, run, test, and lint commands

- Install editable package from the repository root:
  ```powershell
  pip install -e .
  ```
- Show CLI help:
  ```powershell
  speakerops --help
  ```
- Run the core smoke workflow:
  ```powershell
  speakerops init
  speakerops new "Securing Your First Agentic CLI"
  speakerops research talks\securing-your-first-agentic-cli
  speakerops generate cfp talks\securing-your-first-agentic-cli
  speakerops generate outline talks\securing-your-first-agentic-cli
  speakerops review talks\securing-your-first-agentic-cli
  ```
- Compile-check the package:
  ```powershell
  python -m compileall speakerops
  ```
- There is currently no configured test suite or lint command in `pyproject.toml`.

## High-level architecture

- `speakerops.cli` is the Typer entry point exposed by `pyproject.toml` as `speakerops = "speakerops.cli:run"`. It owns command routing, Rich terminal output, and orchestration between config, file storage, prompts, LLMs, and web search.
- `speakerops.config` manages `.speakerops\speakerops.yaml`, model settings, and environment overrides. `speakerops init` writes the packaged profile template and creates `talks\`.
- `speakerops.files` is the Markdown/YAML persistence layer. Generated talk workspaces use `talk.yaml` plus `idea.md`, `research.md`, `cfp.md`, `outline.md`, and `review.md`; these files are also the app's memory.
- `speakerops.prompts` builds the prompt context by combining the speaker profile, talk metadata, and existing Markdown artefacts. Generation commands should go through these prompt helpers instead of duplicating prompt strings in the CLI.
- `speakerops.llm` defines the `LLMClient` protocol. `create_llm_client()` selects GitHub Models, OpenAI, or the local deterministic fallback based on profile settings, environment variables, and the local `api.key` OpenAI fallback.
- `speakerops.web` defines `WebSearchClient` and the current DuckDuckGo-backed implementation. `research` formats search results, then asks the LLM layer to write `research.md`.
- YAML templates live under `speakerops\templates\` and are included as package data. Load them through `importlib.resources` via `read_template()` rather than filesystem-relative paths.

## Key conventions

- This repository is intentionally an unsafe MVP. Do not add filesystem restrictions, path allowlists, network allowlists, approval gates, audit logging, sandboxing, or tool restrictions unless the project stage changes.
- Keep files as the source of memory. Commands should read the current profile, `talk.yaml`, and relevant Markdown files before generating or reviewing artefacts.
- Use `pathlib.Path` and UTF-8 reads/writes via the helpers in `speakerops.files`.
- Generation commands overwrite their target Markdown files without prompting. `chat /save` appends timestamped notes to `idea.md`.
- Provider failures should degrade to the local draft fallback rather than preventing artefact generation.
- Model configuration comes from `.speakerops\speakerops.yaml`, with `SPEAKEROPS_MODEL_PROVIDER` and `SPEAKEROPS_MODEL` taking precedence. Provider credentials come from `GITHUB_TOKEN`, `OPENAI_API_KEY`, or project-root `api.key` for OpenAI.
- Keep CLI output concise and Rich-formatted, matching the current command style.
