# SpeakerOps Demo Runbook

Use this as the low-thinking checklist for conference day.

## 1. Ready-to-go check

Open PowerShell and run:

```powershell
cd C:\Projects\SpeakerOps-Cli
.\.venv\Scripts\Activate.ps1
speakerops --version
speakerops --help
```

Expected:

- Prompt shows `(.venv)`.
- `speakerops --version` prints `speakerops 0.1.0`.
- `speakerops --help` shows the SpeakerOps banner and command list.

If `speakerops` is not found, run:

```powershell
cd C:\Projects\SpeakerOps-Cli
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\Activate.ps1
speakerops --help
```

If activation is awkward, use the direct executable:

```powershell
C:\Projects\SpeakerOps-Cli\.venv\Scripts\speakerops.exe --help
```

Optional sanity checks:

```powershell
git --no-pager status --short --branch
speakerops config
speakerops config --test-api
```

Do not show `api.key` on screen.

## 2. Live demo path

### Demo 1: Open with the CLI and safety story

Say: "SpeakerOps is a local, file-backed CLI assistant for conference talk development. The important part is not just that it generates text, but that it does so inside explicit safety boundaries."

Run:

```powershell
speakerops --help
```

Point out:

- The banner makes the tool feel like a real CLI product.
- The commands map to the talk workflow: idea, research, CFP, outline, review.
- This is intentionally local and file-based.

### Demo 2: Initialise or show configuration

If the repo is already initialised, prefer:

```powershell
speakerops config
```

If using a clean folder, run:

```powershell
speakerops init
speakerops config
```

Point out:

- `.speakerops\speakerops.yaml` stores the profile and safety policy.
- Model provider settings can use OpenAI, GitHub Models, or the local fallback.
- The tool still works without credentials by producing local draft output.

### Demo 3: Create a talk workspace

For a clean live demo:

```powershell
speakerops new "Securing Your First Agentic CLI" --conference AgentCon --audience "platform engineers" --duration 30
speakerops config
```

Point out:

- New talks become the current talk automatically.
- The talk workspace is under `talks\`.
- Files are the application's memory.

If the talk already exists, either use it:

```powershell
speakerops use talks\securing-your-first-agentic-cli
speakerops config
```

or create a timestamped demo talk:

```powershell
speakerops new "SpeakerOps Demo Safety Walkthrough" --conference AgentCon --audience "platform engineers" --duration 30
```

### Demo 4: Chat ideation

Run:

```powershell
speakerops chat
```

Try these prompts:

```text
I want this talk to explain what went wrong when I first built an agentic CLI too quickly.
```

```text
Help me make the security story practical for platform engineers.
```

```text
/context
```

```text
/save
```

```text
/exit
```

Point out:

- The prompt shows the current talk and status.
- `/context` shows the file-backed memory.
- `/save` appends useful notes to `idea.md`.

### Demo 5: Generate artefacts

Run these one at a time:

```powershell
speakerops research
speakerops generate cfp
speakerops generate outline
speakerops review
```

If prompted to apply a preview, type:

```text
y
```

Point out:

- Generated content goes through preview/review before writing.
- Existing artefacts are not silently overwritten.
- The review command also shows trust classification.

### Demo 6: Show trust boundaries

Run:

```powershell
speakerops trust
```

Point out:

- Trusted inputs are config, policy, talk metadata, built-in prompts, and direct user commands.
- Untrusted inputs include web results, imported notes, uploaded documents, and generated research material.
- The model is not treated as an all-powerful actor with arbitrary file or tool access.

### Demo 7: Prompt injection safety demo

Run:

```powershell
speakerops demo prompt-injection
```

Say: "This is the difference between source material and instructions. The suspicious text is preserved as content, but wrapped as untrusted context before model use."

Point out:

- The malicious-looking text is not executed.
- It is labelled as untrusted source material.
- This is a simple but explainable safety boundary.

### Demo 8: Show generated files

Run:

```powershell
Get-ChildItem talks
Get-ChildItem talks\securing-your-first-agentic-cli
```

If using a different talk slug, adjust the path shown by `speakerops config`.

Expected files:

- `talk.yaml`
- `idea.md`
- `research.md`
- `cfp.md`
- `outline.md`
- `review.md`
- `provenance.yaml`

## 3. Recovery notes

### If `speakerops` runs the wrong version

Run:

```powershell
Get-Command speakerops
```

Expected source:

```text
C:\Projects\SpeakerOps-Cli\.venv\Scripts\speakerops.exe
```

If not, activate the venv again:

```powershell
cd C:\Projects\SpeakerOps-Cli
.\.venv\Scripts\Activate.ps1
```

### If PowerShell blocks activation

Run this for the current PowerShell process only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### If the model/API fails

Say: "This is designed to degrade safely. Provider failures fall back to local draft generation so the workflow can continue."

Then continue with:

```powershell
speakerops generate cfp
speakerops generate outline
```

### If research network access is denied

Say: "That is the network allowlist doing its job. Research requests are policy checked and logged."

Then continue with:

```powershell
speakerops review
speakerops trust
```

### If generated output is weak

Do not apologise to the room. Say:

"The point of this demo is the operating model: bounded tools, explicit writes, local files as memory, trust labels, auditability, and provenance. Better model output is a provider choice; safer execution is the architecture choice."

### If you need the shortest safe demo

Run only:

```powershell
cd C:\Projects\SpeakerOps-Cli
.\.venv\Scripts\Activate.ps1
speakerops --help
speakerops config
speakerops new "Securing Your First Agentic CLI" --conference AgentCon --audience "platform engineers" --duration 30
speakerops chat
```

Inside chat:

```text
Help me frame this as a safety story for platform engineers.
/save
/outline
/review
/exit
```

Then:

```powershell
speakerops trust
speakerops demo prompt-injection
```

## 4. Speaker notes

Keep returning to these points:

- SpeakerOps is deliberately local and file-backed.
- Files are memory, not hidden state.
- Commands are explicit; the model does not choose arbitrary tools.
- Writes are bounded to known talk artefacts.
- Existing generated files go through preview/review before overwrite.
- Untrusted content is wrapped before model use.
- Generated content is scanned for likely secrets.
- Approved generated artefacts get provenance records.
- Audit logs record meaningful operations.

Useful one-liner:

```text
The demo is not "look, an AI wrote my CFP"; it is "look, we can design the environment so an AI assistant has useful power without arbitrary power."
```

## 5. Final pre-stage checklist

- Laptop plugged in.
- Terminal font large enough.
- PowerShell opened at `C:\Projects\SpeakerOps-Cli`.
- Venv activated.
- `speakerops --help` shows the banner.
- Browser tabs and notifications closed.
- API key not visible.
- Backup recording ready if live network/model calls fail.
- Water nearby.
