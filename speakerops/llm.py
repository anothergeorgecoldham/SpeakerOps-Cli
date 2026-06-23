from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import requests

from speakerops.config import project_root


class LLMClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        ...


@dataclass(frozen=True)
class LLMConnectionCheck:
    ok: bool
    message: str


@dataclass
class LocalDraftLLMClient:
    model: str = "local-draft"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        lowered = user_prompt.lower()
        if "requested task: generate or update cfp.md" in lowered:
            return _local_cfp(user_prompt)
        if "requested task: generate or update outline.md" in lowered:
            return _local_outline(user_prompt)
        if "requested task: review the current talk package" in lowered:
            return _local_review(user_prompt)
        if "requested task: write research.md" in lowered:
            return _local_research(user_prompt)
        if "summarize" in lowered:
            return "The session explored the talk narrative, target audience, practical examples, and next artefacts to refine."
        return (
            "That sounds like a useful starting point. What audience do you want to shape it for first: "
            "security architects, platform engineers, developers, or a broader community audience?"
        )


@dataclass
class ChatCompletionsClient:
    provider: str
    model: str
    api_key: str
    endpoint: str
    fallback: LocalDraftLLMClient

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.strip():
                return content.strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            return f"_Provider '{self.provider}' failed ({exc}). Using local draft fallback._\n\n{self.fallback.complete(system_prompt, user_prompt)}"
        return self.fallback.complete(system_prompt, user_prompt)


def create_llm_client(provider: str, model: str) -> LLMClient:
    fallback = LocalDraftLLMClient(model="local-draft")
    normalized = provider.lower().strip()
    if normalized in {"github", "github_models", "github-models"}:
        token = os.getenv("GITHUB_TOKEN")
        if token:
            return ChatCompletionsClient(
                provider="github_models",
                model=model,
                api_key=token,
                endpoint="https://models.github.ai/inference/chat/completions",
                fallback=fallback,
            )
    if normalized == "openai":
        token = _openai_api_key()
        if token:
            return ChatCompletionsClient(
                provider="openai",
                model=model,
                api_key=token,
                endpoint="https://api.openai.com/v1/chat/completions",
                fallback=fallback,
            )
    return fallback


def check_llm_connection(provider: str, model: str) -> LLMConnectionCheck:
    normalized = provider.lower().strip()
    if normalized in {"", "local", "local-draft"}:
        return LLMConnectionCheck(True, "Using local draft fallback; no API key is required.")

    endpoint = ""
    token = ""
    display_provider = provider
    if normalized in {"github", "github_models", "github-models"}:
        display_provider = "github_models"
        endpoint = "https://models.github.ai/inference/chat/completions"
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            return LLMConnectionCheck(False, "GITHUB_TOKEN is not set.")
    elif normalized == "openai":
        display_provider = "openai"
        endpoint = "https://api.openai.com/v1/chat/completions"
        token = _openai_api_key() or ""
        if not token:
            return LLMConnectionCheck(False, "OPENAI_API_KEY is not set and api.key was not found at the project root.")
    else:
        return LLMConnectionCheck(False, f"Unknown model provider '{provider}'.")

    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a connection health check."},
            {"role": "user", "content": "Reply with OK."},
        ],
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except requests.HTTPError as exc:
        return LLMConnectionCheck(False, f"{display_provider} API check failed: {_http_error_message(exc)}")
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        return LLMConnectionCheck(False, f"{display_provider} API check failed: {exc}")
    if not isinstance(content, str) or not content.strip():
        return LLMConnectionCheck(False, f"{display_provider} API check returned an empty response.")
    return LLMConnectionCheck(True, f"{display_provider} API check succeeded with model {model}.")


def _http_error_message(exc: requests.HTTPError) -> str:
    response = exc.response
    if response is None:
        return str(exc)
    try:
        data = response.json()
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if message:
                return f"{response.status_code} {message}"
    except ValueError:
        pass
    body = response.text.strip()
    if body:
        return f"{response.status_code} {body[:500]}"
    return str(exc)


def _openai_api_key() -> str | None:
    token = os.getenv("OPENAI_API_KEY")
    if token and token.strip():
        return token.strip()

    key_path = project_root() / "api.key"
    if key_path.exists():
        file_token = key_path.read_text(encoding="utf-8").strip()
        if file_token:
            return file_token

    return None


def _field(prompt: str, name: str, default: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.*)$", prompt)
    if not match:
        return default
    value = match.group(1).strip().strip("'\"")
    return value or default


def _local_cfp(prompt: str) -> str:
    title = _field(prompt, "title", "Working Talk Title")
    audience = _field(prompt, "target_audience", "security architects, cloud engineers, platform teams, and technical community audiences")
    conference = _field(prompt, "target_conference", "the target conference")
    return f"""# CFP Submission

## Title

{title}

## Abstract

Agentic command-line tools can move fast from idea to execution, but the first version is often intentionally naive: broad file access, unconstrained network calls, and no approval gates. This talk uses {title} as a practical teaching device. We will build a simple workflow, inspect where autonomy creates risk, and identify the boring controls that make later versions reviewable and trustworthy.

## Elevator Pitch

A practical walkthrough of an unsafe agentic CLI and the security lessons it makes visible.

## Audience

{audience}.

## Learning Outcomes

- Recognise common risk points in naive agentic CLIs.
- Explain why files, reviewability, and workflow boundaries matter.
- Translate a rough demo into a staged security improvement plan.

## Why This Talk / Why Now

Teams are rapidly experimenting with AI-assisted automation. For {conference}, this gives attendees a concrete way to understand required controls by first seeing what an uncontrolled version can do.

## Speaker Fit

The speaker brings a practical cloud security perspective, with emphasis on clear trade-offs, implementation patterns, and avoiding hype.
"""


def _local_outline(prompt: str) -> str:
    audience = _field(prompt, "target_audience", "security architects, cloud engineers, platform teams, and technical community audiences")
    duration = _field(prompt, "duration_minutes", "30")
    return f"""# Talk Outline

## Talk Thesis

Agentic systems need boring controls before exciting autonomy, and an unsafe MVP is a useful way to understand why.

## Audience

{audience}.

## Timing

{duration} minutes.

## Structure

### Opening

Introduce the promise and risk of agentic CLIs with a concrete speaker-workflow example.

### Act 1

Build the naive workflow: profile, talk workspace, chat, research, generation, and review.

### Act 2

Show what is unsafe: unrestricted file reads/writes, unconstrained network use, no approvals, and no audit trail.

### Act 3

Map each risk to a future control without losing the useful workflow.

### Closing

Reframe security as delivery enablement: keep the workflow useful, then make it governable.

## Demo Ideas

- Generate a talk package from a rough title.
- Run unconstrained research and compare it with reviewable notes.
- Show where a later policy layer would intercept actions.

## Key Takeaways

- The workflow is often more important than the model.
- Reviewable files are simple but powerful control points.
- Start by understanding autonomy, then constrain it deliberately.

## Possible Q&A

- Which controls should be added first?
- How much autonomy is appropriate for internal tools?
- What should be logged or reviewed in a secured version?
"""


def _local_research(prompt: str) -> str:
    title = _field(prompt, "title", "this talk")
    return f"""# Research Notes

## Useful References

- OWASP Top 10 for Large Language Model Applications: useful for framing prompt injection, insecure output handling, and excessive agency.
- NIST AI Risk Management Framework: useful for governance language and risk framing.
- Microsoft guidance on responsible AI and Zero Trust: useful for connecting AI systems to practical enterprise controls.

## Short Summaries

For {title}, the central research thread is that agentic tools combine model output with actions. The risk is not only inaccurate text; it is the ability to read, write, call services, and make changes without sufficient boundaries.

## Suggested Citations

Use OWASP for application risk categories, NIST for risk-management framing, and vendor architecture guidance for concrete control patterns.

## Possible Examples / Incidents

- Prompt injection causing an assistant to follow instructions from untrusted content.
- Overbroad filesystem access exposing unrelated project files.
- Unreviewed generated artefacts being treated as authoritative.

## Relevance to the Talk

These references support a staged narrative: first show the unsafe workflow, then explain the controls needed to make it suitable for real teams.
"""


def _local_review(prompt: str) -> str:
    title = _field(prompt, "title", "the talk")
    return f"""# Review Summary

## Concise Summary

{title} has a clear practical hook: use an intentionally unsafe agentic CLI to make security controls concrete. The strongest angle is the staged contrast between useful autonomy and governed autonomy.

## Clarity of Thesis

Strong. The thesis should be stated early: agentic systems need boring controls before exciting autonomy.

## Audience Fit

Good fit for security architects, cloud engineers, platform teams, and technical communities.

## Novelty

The unsafe-first framing is distinctive because it shows risk through a working workflow rather than abstract warnings.

## Practical Value

High if the demo clearly maps each unsafe behaviour to a later control.

## Structure

Use a three-act structure: naive build, risk discovery, controlled future state.

## Weak Spots

Avoid spending too long on implementation details. Keep the security lessons visible.

## Missing Evidence

Add citations for OWASP LLM risks, NIST AI RMF, and practical Zero Trust guidance.

## Suggested Next Steps

Refine the demo script, collect two or three authoritative references, and sharpen the before/after control table.
"""
