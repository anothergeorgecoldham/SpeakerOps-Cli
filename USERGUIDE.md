# SpeakerOps User Guide

SpeakerOps helps turn a rough talk idea into a file-based talk workspace. The
main workflow is: create a profile, create a talk, discuss the idea, then
generate research notes, CFP copy, an outline, and a review.

For the stage-by-stage safety history behind the project, see
[RELEASE_NOTES.md](RELEASE_NOTES.md).

## Install and initialise

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
speakerops init
```

`speakerops init` runs a profile setup wizard, then creates `.speakerops/speakerops.yaml`
and `talks/`.
Use `speakerops init --non-interactive` when you need default values for demos,
automation, or CI.

`speakerops --help`, `speakerops init`, and `speakerops config` show the
SpeakerOps banner with a cyan-to-magenta terminal gradient when colour output is
available.

## Configure the model

SpeakerOps works without credentials by using the local draft fallback. To use
OpenAI with a local `api.key` file:

```bash
speakerops config --use-openai
printf '%s\n' "your-openai-api-key" > api.key
speakerops config --test-api
```

`api.key` is ignored by Git. You can also use environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export SPEAKEROPS_MODEL_PROVIDER="openai"
export SPEAKEROPS_MODEL="gpt-4o-mini"
```

Environment variables override `.speakerops/speakerops.yaml`.

## Create and select a talk

Create a talk:

```bash
speakerops new "Securing Your First Agentic CLI"
```

New talks automatically become the current talk. Most commands use the current
talk when you do not pass a path.

Check the current talk:

```bash
speakerops config
```

Switch current talk:

```bash
speakerops use talks/securing-your-first-agentic-cli
```

You can also pass a talk path directly to commands when you want to override the
current talk.

## Talk workspace files

Each talk workspace contains:

| File | Purpose |
| --- | --- |
| `talk.yaml` | Talk metadata such as title, audience, conference, duration, and status. |
| `idea.md` | Notes from chat and manual ideation. |
| `research.md` | Research notes and references. |
| `cfp.md` | CFP submission draft. |
| `outline.md` | Talk outline draft. |
| `review.md` | Review summary and suggested improvements. |

These files are the app's memory. Commands read the current files before
generating new content.

## Conversational workflow

Start chat:

```bash
speakerops chat
```

Normal chat is intentionally conversational. It should help narrow the topic,
audience, angle, and structure before generating longer artefacts.

The chat prompt shows the current workspace context in coloured segments:

```text
 speakerops  securing-your-first-agentic-cli  idea  you 
```

Useful chat commands:

| Command | Action |
| --- | --- |
| `/help` | Show chat commands. |
| `/context` | Show loaded profile, talk, and Markdown context sizes. |
| `/save` | Summarise the current chat into `idea.md`. |
| `/research` | Generate `research.md`. |
| `/cfp` | Generate `cfp.md`. |
| `/outline` | Generate `outline.md`. |
| `/review` | Generate `review.md`. |
| `/exit` | Quit chat. |

Use chat to shape the idea first, then run an artefact command when you are
ready. For example:

```text
you> I want this to be about what I learned building my first CLI agent.
assistant> ...
you> Let's focus on platform engineers.
assistant> ...
you> /outline
```

## Standalone artefact commands

You can also generate artefacts outside chat:

```bash
speakerops research
speakerops generate cfp
speakerops generate outline
speakerops review
```

These commands use the current talk by default. Pass a talk folder if you want
to target a specific workspace:

```bash
speakerops review talks/securing-your-first-agentic-cli
```

## Review before write

Generated artefacts are written to `.preview` files first. SpeakerOps shows the
target, preview path, and a diff when the target already exists. It then asks
whether to apply the preview.

Answer `y` or `yes` to apply the generated content. Any other answer keeps the
preview and leaves the original file unchanged.

## Safety boundaries

The chat artefact commands do not give the model arbitrary tool access.

The user must type explicit slash commands such as `/cfp` or `/review`. Those
commands call the same internal workflows as the standalone CLI commands. The
LLM generates content, but it does not choose arbitrary tools, commands, or file
paths.

Writes are bounded to known talk artefacts through the internal tool allowlist
and review-before-write flow.

## Hardened controls

SpeakerOps reads hardened control settings from `.speakerops/speakerops.yaml`:

```yaml
security:
  hardened: true
  allowed_operators: []
  scan_generated_content: true
  provenance_enabled: true
```

`allowed_operators` is empty by default, which logs the local operator but does
not restrict usage. To restrict talk operations to specific local users, add the
OS username or `SPEAKEROPS_OPERATOR` value:

```yaml
security:
  allowed_operators:
    - georgecoldham
```

Set `security.hardened` to `false` only for local experiments where you
intentionally want to disable operator restrictions, generated-content secret
scanning, and provenance records.

Generated artefacts are scanned for likely secrets before previews are written.
If a generated response appears to contain an API key, token, private key, or
high-entropy secret-like value, SpeakerOps denies the write and logs the result.

When generated content is approved, SpeakerOps writes a provenance record to
`provenance.yaml` in the talk workspace. The record includes the timestamp,
operator, action, target artefact, generated content hash, and hashes of the
input talk files.

## Troubleshooting

If `speakerops chat` appears idle, it is usually waiting for the model response.
The CLI shows a `Thinking...` status while requests are in progress.

If config cannot be found from a subdirectory, run:

```bash
speakerops config
```

SpeakerOps should discover the project root from inside the repo or `.speakerops/`.

If OpenAI is configured but generation falls back to local drafts, check:

```bash
speakerops config --test-api
```

Do not commit API keys or store secrets in talk files.
