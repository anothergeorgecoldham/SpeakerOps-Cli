# SpeakerOps

SpeakerOps is a minimal Python CLI for helping technical speakers turn rough talk ideas into useful conference artefacts: ideation notes, research notes, CFP submissions, talk outlines, and review summaries.

This is an early unsafe MVP. It intentionally does not include filesystem restrictions, path allowlisting, network allowlisting, approval gates, audit logging, sandboxing, or tool restrictions. Those controls are expected in a later security-focused stage.

## Install

Requires Python 3.11 or later.

```bash
pip install -e .
```

## Quickstart

```bash
speakerops init
speakerops new "Securing Your First Agentic CLI"
speakerops chat talks/securing-your-first-agentic-cli
speakerops research talks/securing-your-first-agentic-cli
speakerops generate cfp talks/securing-your-first-agentic-cli
speakerops generate outline talks/securing-your-first-agentic-cli
speakerops review talks/securing-your-first-agentic-cli
```

## Example workflow

1. Initialise a local profile with `speakerops init`.
2. Create a talk workspace with `speakerops new "Talk Title" --conference NDC --audience "security engineers" --duration 30`.
3. Use `speakerops chat <talk-folder>` to explore the idea and save useful notes to `idea.md`.
4. Run `speakerops research <talk-folder>` to populate `research.md`.
5. Generate a CFP and outline with `speakerops generate cfp <talk-folder>` and `speakerops generate outline <talk-folder>`.
6. Review the current package with `speakerops review <talk-folder>`.

## Configuration

`speakerops init` creates `.speakerops/speakerops.yaml`. The profile stores speaker details, interests, preferred audiences, tone, speaking style, and model settings.

Model settings can also be supplied with environment variables:

```bash
GITHUB_TOKEN=
OPENAI_API_KEY=
SPEAKEROPS_MODEL_PROVIDER=
SPEAKEROPS_MODEL=
```

The MVP includes a simple provider abstraction. It can call GitHub Models or OpenAI-compatible chat completions when credentials are available, and falls back to a local deterministic draft generator when they are not.

## Current limitations

- This is intentionally permissive and unsafe.
- Research uses a basic web-search abstraction and may fall back to placeholder references.
- The LLM abstraction is deliberately simple and file-based; Markdown files are the memory.
- There is no GitHub integration, publishing, slide generation, database, vector search, plugin architecture, or multi-agent framework.
