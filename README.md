# SpeakerOps

SpeakerOps is a minimal Python CLI for helping technical speakers turn rough talk ideas into useful conference artefacts: ideation notes, research notes, CFP submissions, talk outlines, and review summaries.

SpeakerOps started as an early unsafe MVP without filesystem restrictions, path allowlisting, network allowlisting, approval gates, audit logging, sandboxing, or tool restrictions. Those controls are expected to be added incrementally in later security-focused stages.

Stage 2 adds workspace boundary protection so talk operations are restricted to the selected talk folder.

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

The MVP includes a simple provider abstraction. It can call GitHub Models or OpenAI-compatible chat completions when credentials are available, and falls back to a local deterministic draft generator when they are not. For OpenAI, SpeakerOps uses `OPENAI_API_KEY` first and then falls back to a local `api.key` file in the project root.

## Using a real LLM

SpeakerOps works without credentials by using a local draft fallback, but real model output requires either a GitHub Models token or an OpenAI API key.

### Option 1: GitHub Models

1. Read the GitHub Models documentation: <https://docs.github.com/en/github-models>
2. Create a GitHub personal access token: <https://github.com/settings/tokens>
3. Give the token access required for GitHub Models in your account or organization.
4. Set the environment variables:

```powershell
$env:GITHUB_TOKEN="your-github-token"
$env:SPEAKEROPS_MODEL_PROVIDER="github_models"
$env:SPEAKEROPS_MODEL="openai/gpt-5-nano"
```

### Option 2: OpenAI

1. Create or sign in to an OpenAI account: <https://platform.openai.com/>
2. Create an API key: <https://platform.openai.com/api-keys>
3. Check model availability and pricing before use: <https://platform.openai.com/docs/models>
4. Set the environment variables:

```powershell
$env:OPENAI_API_KEY="your-openai-api-key"
$env:SPEAKEROPS_MODEL_PROVIDER="openai"
$env:SPEAKEROPS_MODEL="gpt-4o-mini"
```

Alternatively, put the OpenAI API key in `api.key` at the project root. This file is ignored by Git.

### Check the active settings

```powershell
speakerops config
speakerops generate cfp talks\securing-your-first-agentic-cli
```

Do not commit API keys or store them in generated talk files.

## Audit logging

SpeakerOps writes a plain text audit log to `.speakerops/audit.log`. The log records talk file reads, writes, creates, policy denials, and high-level actions such as research, CFP generation, outline generation, and review.

## Overwrite approval

When a generated artefact already exists, SpeakerOps asks before overwriting it. The default answer is No, and approval decisions are written to the audit log.

## Tool allowlisting

SpeakerOps routes talk workflow actions through a small internal tool allowlist. Registered tools include talk file reads and writes, talk file listing, CFP generation, outline generation, research, and review; unregistered tool calls are denied and logged.

## Network allowlisting

Research network requests are checked against the `network` section in `.speakerops/speakerops.yaml`. In `allowlist` mode, requests are only allowed for configured domains, and allowed or denied requests are written to the audit log.

## Sensitive path denylisting

Workspace file access also checks the `paths.deny` patterns in `.speakerops/speakerops.yaml`. Sensitive paths such as environment files, private keys, SSH material, and Git credential files are denied even when they are inside the selected talk folder.

## Review before write

Generated artefacts are written to `.preview` files first. SpeakerOps shows the target, preview path, and a unified diff when the target already exists, then asks whether to apply the preview. Denied previews are kept for review and the original file is left unchanged.

## Trusted and untrusted content

SpeakerOps treats configuration, policy, talk metadata, built-in prompts, and user commands as trusted instructions. Web results, research notes, imported Markdown, copied CFP pages, downloaded pages, and uploaded documents are treated as untrusted source material, wrapped before model use, and logged in the audit log.

## License

SpeakerOps is licensed under the MIT License. See [LICENSE](LICENSE).

## Trust classification

SpeakerOps tracks content sources as trusted or untrusted using simple rules. Run `speakerops trust <talk-folder>` to see trusted sources, untrusted sources, counts, and origins for a talk. The review command also prints a trust summary.

## Current limitations

- This is intentionally permissive and unsafe.
- Research uses a basic web-search abstraction and may fall back to placeholder references.
- The LLM abstraction is deliberately simple and file-based; Markdown files are the memory.
- There is no GitHub integration, publishing, slide generation, database, vector search, plugin architecture, or multi-agent framework.
