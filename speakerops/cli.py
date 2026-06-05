from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from speakerops import __version__
from speakerops.config import init_profile, load_profile, model_settings, profile_path
from speakerops.files import (
    initial_markdown,
    load_talk_context,
    PolicyViolation,
    slugify,
    utc_timestamp,
    WorkspacePolicy,
    write_text,
    write_yaml,
)
from speakerops.llm import create_llm_client
from speakerops.prompts import chat_prompt, cfp_prompt, context_block, outline_prompt, research_prompt, review_prompt, system_prompt
from speakerops.web import DuckDuckGoSearchClient, format_results


app = typer.Typer(help="SpeakerOps unsafe MVP CLI.")
generate_app = typer.Typer(help="Generate talk artefacts.")
app.add_typer(generate_app, name="generate")
console = Console()


@app.callback()
def main(version: bool = typer.Option(False, "--version", help="Show version and exit.")) -> None:
    if version:
        console.print(f"speakerops {__version__}")
        raise typer.Exit()


@app.command()
def init() -> None:
    """Initialise SpeakerOps in the current directory."""
    path = init_profile()
    console.print("[bold green]Initialised SpeakerOps[/bold green]")
    console.print(f"Profile: {path}")
    console.print("Created: talks/")


@app.command(name="config")
def config_command() -> None:
    """Print the loaded profile and model settings."""
    profile = _profile_or_exit()
    settings = model_settings(profile)

    table = Table(title="SpeakerOps configuration")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("Profile path", str(profile_path()))
    table.add_row("Speaker name", str(profile.get("name", "")))
    table.add_row("Role", str(profile.get("role", "")))
    table.add_row("Model provider", settings.provider)
    table.add_row("Model", settings.model)
    primary = profile.get("interests", {}).get("primary", [])
    table.add_row("Primary interests", ", ".join(primary) if isinstance(primary, list) else str(primary))
    console.print(table)


@app.command()
def new(
    title: str,
    conference: str = typer.Option("", "--conference", "-c", help="Target conference."),
    audience: str = typer.Option("", "--audience", "-a", help="Target audience."),
    duration: int = typer.Option(30, "--duration", "-d", help="Talk duration in minutes."),
) -> None:
    """Create a new talk workspace."""
    slug = slugify(title)
    talk_dir = Path("talks") / slug
    talk_dir.mkdir(parents=True, exist_ok=True)

    talk = {
        "title": title,
        "slug": slug,
        "status": "idea",
        "created_at": utc_timestamp(),
        "target_audience": audience,
        "target_conference": conference,
        "duration_minutes": duration,
        "description": "",
    }
    write_yaml(talk_dir / "talk.yaml", talk)
    for name, content in initial_markdown(title).items():
        write_text(talk_dir / name, content)

    console.print("[bold green]Created talk workspace:[/bold green]")
    console.print(str(talk_dir))
    console.print("Generated: talk.yaml, idea.md, research.md, cfp.md, outline.md, review.md")


@app.command()
def chat(talk_path: Path) -> None:
    """Start an interactive ideation session for a talk."""
    profile = _profile_or_exit()
    talk, markdown, policy = _talk_or_exit(talk_path)
    settings = model_settings(profile)
    llm = create_llm_client(settings.provider, settings.model)
    transcript: list[str] = []

    console.print("[bold green]SpeakerOps chat started.[/bold green]")
    console.print("Type /save to save notes.")
    console.print("Type /exit to quit.")

    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not message:
            continue
        if message == "/exit":
            break
        if message == "/context":
            _print_context_summary(profile, talk, markdown)
            continue
        if message == "/save":
            summary_prompt = "Summarize the useful outcomes from this session as concise Markdown notes."
            summary = llm.complete(system_prompt(), chat_prompt(context_block(profile, talk, markdown), "\n".join(transcript), summary_prompt))
            saved_at = utc_timestamp()
            notes = f"\n\n## Chat Notes - {saved_at}\n\n{summary}\n"
            policy.append_text("idea.md", notes)
            markdown["idea.md"] = markdown.get("idea.md", "") + notes
            console.print("[green]Saved session notes to idea.md[/green]")
            continue

        context = context_block(profile, talk, markdown)
        response = llm.complete(system_prompt(), chat_prompt(context, "\n".join(transcript), message))
        transcript.extend([f"you: {message}", f"assistant: {response}"])
        console.print(f"assistant> {response}")


@app.command()
def research(talk_path: Path) -> None:
    """Gather supporting research for a talk."""
    profile = _profile_or_exit()
    talk, markdown, policy = _talk_or_exit(talk_path)
    settings = model_settings(profile)
    llm = create_llm_client(settings.provider, settings.model)
    query = " ".join(
        part
        for part in [
            str(talk.get("title", "")),
            str(talk.get("target_audience", "")),
            str(talk.get("target_conference", "")),
            "conference talk research references examples",
        ]
        if part
    )
    results = DuckDuckGoSearchClient().search(query)
    content = llm.complete(system_prompt(), research_prompt(context_block(profile, talk, markdown), format_results(results)))
    policy.write_text("research.md", content)
    console.print("[bold green]Generated:[/bold green] research.md")


@generate_app.command()
def cfp(talk_path: Path) -> None:
    """Generate or update cfp.md."""
    profile, talk, markdown, llm, policy = _generation_inputs(talk_path)
    content = llm.complete(system_prompt(), cfp_prompt(context_block(profile, talk, markdown)))
    policy.write_text("cfp.md", content)
    console.print("[bold green]Generated:[/bold green] cfp.md")


@generate_app.command()
def outline(talk_path: Path) -> None:
    """Generate or update outline.md."""
    profile, talk, markdown, llm, policy = _generation_inputs(talk_path)
    content = llm.complete(system_prompt(), outline_prompt(context_block(profile, talk, markdown)))
    policy.write_text("outline.md", content)
    console.print("[bold green]Generated:[/bold green] outline.md")


@app.command()
def review(talk_path: Path) -> None:
    """Review the current talk package."""
    profile, talk, markdown, llm, policy = _generation_inputs(talk_path)
    content = llm.complete(system_prompt(), review_prompt(context_block(profile, talk, markdown)))
    policy.write_text("review.md", content)
    console.print("[bold green]Generated:[/bold green] review.md")
    summary = _first_non_empty_lines(content, count=4)
    if summary:
        console.print("\n".join(summary))


def _generation_inputs(talk_path: Path):
    profile = _profile_or_exit()
    talk, markdown, policy = _talk_or_exit(talk_path)
    settings = model_settings(profile)
    llm = create_llm_client(settings.provider, settings.model)
    return profile, talk, markdown, llm, policy


def _profile_or_exit() -> dict:
    try:
        return load_profile()
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc


def _talk_or_exit(talk_path: Path):
    try:
        policy = WorkspacePolicy(talk_path)
        talk, markdown = load_talk_context(policy)
        return talk, markdown, policy
    except (FileNotFoundError, PolicyViolation, ValueError) as exc:
        console.print(f"[red]Could not load talk at {talk_path}: {exc}[/red]")
        raise typer.Exit(1) from exc


def _print_context_summary(profile: dict, talk: dict, markdown: dict[str, str]) -> None:
    console.print(f"Speaker: {profile.get('name', '')} ({profile.get('role', '')})")
    console.print(f"Talk: {talk.get('title', '')}")
    for name, content in markdown.items():
        console.print(f"{name}: {len(content)} characters")


def _first_non_empty_lines(content: str, count: int) -> list[str]:
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
        if len(lines) >= count:
            break
    return lines


def run() -> None:
    app()


if __name__ == "__main__":
    run()
