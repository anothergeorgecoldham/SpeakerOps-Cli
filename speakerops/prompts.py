from __future__ import annotations

from typing import Any

import yaml

from speakerops.audit import AuditLogger
from speakerops.content import prepare_content


def context_block(profile: dict[str, Any], talk: dict[str, Any], markdown: dict[str, str], audit_logger: AuditLogger | None = None) -> str:
    sections = [
        "## Speaker profile",
        prepare_content("speakerops.yaml", yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), audit_logger),
        "## Talk metadata",
        prepare_content("talk.yaml", yaml.safe_dump(talk, sort_keys=False, allow_unicode=True), audit_logger),
    ]
    for name, content in markdown.items():
        if content.strip():
            sections.extend([f"## Existing {name}", prepare_content(name, content, audit_logger)])
    return "\n\n".join(sections)


def system_prompt() -> str:
    return (
        "You are SpeakerOps, a practical assistant for developing technical conference talks. "
        "Use the speaker profile, talk metadata, and existing Markdown files as memory. "
        "Write concise, useful, evidence-aware content in the speaker's tone."
    )


def cfp_prompt(context: str) -> str:
    return f"""{context}

Requested task: Generate or update cfp.md.

Return Markdown with exactly these sections:

# CFP Submission

## Title

## Abstract

## Elevator Pitch

## Audience

## Learning Outcomes

## Why This Talk / Why Now

## Speaker Fit
"""


def outline_prompt(context: str) -> str:
    return f"""{context}

Requested task: Generate or update outline.md.

Return Markdown with exactly these sections:

# Talk Outline

## Talk Thesis

## Audience

## Timing

## Structure

### Opening

### Act 1

### Act 2

### Act 3

### Closing

## Demo Ideas

## Key Takeaways

## Possible Q&A
"""


def review_prompt(context: str) -> str:
    return f"""{context}

Requested task: Review the current talk package.

Write review.md assessing clarity of thesis, audience fit, novelty, practical value, structure, weak spots, missing evidence, and suggested next steps. Start with a concise summary.
"""


def research_prompt(context: str, search_notes: str) -> str:
    return f"""{context}

## Search results

{search_notes}

Requested task: Write research.md for this talk. Include useful references, short summaries, suggested citations, possible examples/incidents, and relevance to the talk.
"""


def chat_prompt(context: str, transcript: str, message: str) -> str:
    return f"""{context}

## Current chat transcript

{transcript}

User message: {message}

Respond as a practical ideation partner in a conversation, not as a drafting engine.

Default behavior:
- Keep replies short: one or two brief paragraphs, or at most three bullets.
- Ask one focused question when the topic, audience, angle, or structure is still unclear.
- Help narrow the idea before producing outlines, CFP copy, slide structures, or long notes.
- If the user provides only a rough topic or starting idea, do not suggest outlines, demo beats, takeaways, slide structures, or reference lists yet. Reflect the idea briefly, then ask one question to choose the direction.
- Do not produce pages of content unless the user explicitly asks you to draft, outline, generate, write, or list detailed material.
- When the user asks for a draft or structured output, produce only the requested artefact and keep it proportionate.
"""
