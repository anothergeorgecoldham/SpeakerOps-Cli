# SpeakerOps Release Notes by Safety Stage

These notes describe the evolution of SpeakerOps across the tagged versions in
this repository. They are written both as release notes and as talk-prep
material: each stage includes what changed, why it mattered, and the story it
helps tell about moving from a useful but unsafe agentic CLI toward a bounded,
reviewable, safety-focused local agent workflow.

## Stage summary

| Tag | Theme | Core shift |
| --- | --- | --- |
| `v0.1-unsafe-mvp` | Initial unsafe MVP | Proved the file-based talk workflow could work. |
| `v0.2-workspace-boundaries` | Workspace boundaries | Restricted talk operations to the selected talk folder. |
| `v0.3-audit-logging` | Audit logging | Started recording file and workflow actions. |
| `v0.4-approval-gates` | Approval gates | Added human confirmation before overwriting existing files. |
| `v0.5-tool-allowlist` | Tool allowlist | Routed workflow actions through registered internal tools. |
| `v0.6-network-controls` | Network controls | Added allowlisted research network access. |
| `v0.7-sensitive-path-denylist` | Sensitive path denylist | Blocked common secret and credential paths. |
| `v0.8-review-before-write` | Review before write | Generated previews and diffs before applying artefacts. |
| `v0.9-prompt-injection-protection` | Prompt-injection protection | Wrapped untrusted content before model use. |
| `v1.0-trust-classification` | Trust classification | Surfaced trusted and untrusted sources in CLI output. |
| `v1.1-guided-safe-mvp` | Guided safe MVP | Improved setup, configuration, chat UX, current-talk workflow, and user docs. |
| `v1.2-hardened-controls` | Hardened controls | Added local security policy, operator authorization, secret scanning, and provenance. |

## `v0.1-unsafe-mvp` - Initial SpeakerOps MVP

**Commit:** `6ce8750` - `Initial SpeakerOps MVP`

This first version established the basic product idea: a small Python CLI that
helps a technical speaker move from a talk idea to conference artefacts. It
created the core command surface and the file-based workspace model.

**What it introduced**

- Typer-based `speakerops` CLI entry point.
- Local profile initialisation with `.speakerops/speakerops.yaml`.
- Talk workspace creation under `talks/`.
- Generated talk files such as `idea.md`, `research.md`, `cfp.md`,
  `outline.md`, and `review.md`.
- LLM abstraction with a deterministic local fallback.
- Markdown files as the application's working memory.

**Why it mattered**

This stage proved the workflow was useful before adding controls. The CLI could
create a repeatable talk-development workspace and generate useful draft
artefacts from local files and model output.

**Safety posture**

Unsafe by design. The priority was workflow discovery, not enforcement.

**Talk angle**

This is the "make the workflow real first" stage. It is useful because security
controls are easier to explain when there is a working system to constrain.

## `v0.2-workspace-boundaries` - Workspace boundaries

**Commit:** `6bf0dc6` - `Add workspace boundary protection`

This stage added the first meaningful safety boundary: talk file operations were
restricted to the selected talk workspace.

**What changed**

- Introduced workspace path resolution in the file layer.
- Prevented relative-path traversal outside the active talk directory.
- Began treating the talk folder as the explicit operating boundary.
- Updated the README to document the stage.

**Why it mattered**

Without workspace boundaries, a CLI that reads and writes files can accidentally
or maliciously touch unrelated project files. This stage made the talk workspace
the unit of authority.

**Safety posture**

Still early, but no longer completely unconstrained. File access now had a
defined scope.

**Talk angle**

This is the first "boring control": before debating sophisticated policy, make
sure the tool cannot leave the folder it is supposed to operate in.

## `v0.3-audit-logging` - Audit logging

**Commit:** `13ed97d` - `Add audit logging`

This stage added an audit trail for talk file access and high-level workflow
actions.

**What changed**

- Added `speakerops.audit.AuditLogger`.
- Logged file reads, writes, creates, denied policy actions, and workflow events.
- Wrote audit entries to `.speakerops/audit.log`.
- Integrated logging into the workspace file policy.

**Why it mattered**

Automation without a record is difficult to trust. Audit logging made actions
inspectable after the fact and created a foundation for later safety controls.

**Safety posture**

The tool still performed actions directly, but now the actions were visible.

**Talk angle**

This stage supports the line: "If an agent can act, it must leave a trail."

## `v0.4-approval-gates` - Approval gates

**Commit:** `9ccd6ef` - `Add overwrite approval gates`

This stage added human confirmation before overwriting existing artefacts.

**What changed**

- Added `speakerops.approval.ApprovalGate`.
- Prompted before overwriting files.
- Logged approval requirements and approval decisions.
- Preserved existing files when approval was denied.

**Why it mattered**

Generated content can be wrong, overconfident, or simply not what the user
wanted. Human approval introduced a review point before destructive writes.

**Safety posture**

The CLI became less likely to accidentally replace useful work without a user
decision.

**Talk angle**

This stage is about keeping humans in the loop at the point of irreversible
change.

## `v0.5-tool-allowlist` - Tool allowlist

**Commit:** `9ae3f27` - `Add tool allowlist`

This stage routed internal workflow actions through an explicit allowlist.

**What changed**

- Added `speakerops.tools.ToolAllowlist`.
- Registered known internal tools such as reading talk files, writing talk
  files, listing talk files, and generating artefacts.
- Denied unregistered tool calls.
- Logged allowed and denied tool calls.

**Why it mattered**

The CLI moved from direct function calls toward a controlled internal tool
surface. That is an important agent-safety pattern: make capabilities explicit,
small, and auditable.

**Safety posture**

The model still did not receive arbitrary tool access, and the code now had a
bounded place to enforce which actions exist.

**Talk angle**

This is the "capability inventory" stage: if you cannot list what the agent can
do, you cannot govern it.

## `v0.6-network-controls` - Network controls

**Commit:** `1457a4a` - `Add research network controls`

This stage added policy around research network access.

**What changed**

- Added `speakerops.network.NetworkPolicy`.
- Added network configuration in the profile template.
- Checked research URLs against an allowlist.
- Logged allowed and denied network requests.
- Returned local fallback research results when access was denied or failed.

**Why it mattered**

Research features introduce external data flow. This stage made outbound
network access explicit and policy-controlled rather than ambient.

**Safety posture**

Research could still use the web, but only through the configured network
policy.

**Talk angle**

This stage shows how "agentic research" is not just prompting; it is also data
movement and network policy.

## `v0.7-sensitive-path-denylist` - Sensitive path denylist

**Commit:** `8fc9fae` - `Add sensitive path denylist`

This stage blocked common sensitive filenames and credential paths even inside
the selected workspace.

**What changed**

- Added denylist patterns to the profile template.
- Checked paths such as `.env`, `.env.*`, private keys, SSH material, Git
  config, and Git credentials.
- Denied matching reads and writes through workspace policy.
- Logged denied path access.

**Why it mattered**

Workspace boundaries alone are not enough. A secret can exist inside an allowed
workspace. This stage introduced a second layer: sensitive path filtering.

**Safety posture**

The file boundary became more nuanced: allowed workspace, denied sensitive
paths.

**Talk angle**

This is a practical example of layered controls. A boundary reduces scope; a
denylist handles high-risk exceptions inside that scope.

## `v0.8-review-before-write` - Review before write

**Commit:** `1b8dc03` - `Add review before write previews`

This stage changed generated artefact writes to use preview files and diffs.

**What changed**

- Generated content is first written to `.preview` files.
- The CLI prints the target path, preview path, and whether the target exists.
- When a target exists, the CLI prints a unified diff.
- The user explicitly approves applying the preview.
- Denied previews are kept for inspection.

**Why it mattered**

This is stronger than a simple overwrite prompt because the user can inspect
what is about to change. It makes generated output reviewable before it becomes
the official artefact.

**Safety posture**

Generated writes became review-first rather than write-first.

**Talk angle**

This is one of the strongest demo moments: the agent proposes, the user reviews,
and only then does content become part of the workspace.

## `v0.9-prompt-injection-protection` - Prompt-injection protection

**Commit:** `4ee0802` - `Add prompt injection content wrapping`

This stage separated trusted instructions from untrusted source material.

**What changed**

- Added `speakerops.content`.
- Classified sources such as web results and generated Markdown as untrusted.
- Wrapped untrusted content before model use.
- Instructed the model not to follow instructions embedded in untrusted source
  material.
- Added a prompt-injection demo command.

**Why it mattered**

The system uses external and generated content as context. That content can
contain instructions. Wrapping untrusted material reduces the chance that the
model treats source material as commands.

**Safety posture**

Prompt construction became more explicit about instruction hierarchy and
source trust.

**Talk angle**

This stage makes prompt injection concrete: the same text can be useful as
evidence and dangerous as an instruction.

## `v1.0-trust-classification` - Trust classification

**Commit:** `5ce0190` - `Add trust classification reporting`

This stage made trust assignments visible to the user.

**What changed**

- Added trust classification reporting.
- Added `speakerops trust`.
- Printed trusted and untrusted source counts.
- Included trust summary output in review workflows.
- Expanded trust logging.

**Why it mattered**

It is not enough for the code to classify content internally. Users need to see
which sources are trusted, which are untrusted, and why review output should be
interpreted cautiously.

**Safety posture**

The system became more transparent about trust boundaries.

**Talk angle**

This stage supports a key message: "Security controls should be visible enough
for humans to reason about them."

## Untagged commits before `v1.1`

Three useful commits landed after `v1.0` and before the guided workflow tag:

- `49e2fea` - Added the MIT license.
- `24bb645` - Documented LLM setup.
- `4684239` - Added local OpenAI key file support.

These changes improved project readiness and real-model usability. In
particular, local `api.key` support made it easier to use OpenAI without
storing secrets in YAML.

## `v1.1-guided-safe-mvp` - Guided safe MVP

**Commit:** `816d389` - `Add guided CLI workflow improvements`

This tag captures the state after the CLI became much easier to install,
configure, and use interactively.

**What changed**

- Updated install docs to use a virtual environment, avoiding Homebrew Python's
  externally managed environment error.
- Added current-talk support:
  - `speakerops new` sets the created talk as current.
  - Talk commands default to the current talk.
  - `speakerops use <talk-folder>` switches the current talk.
  - `speakerops config` displays the current talk.
- Added project-root discovery so commands work from nested directories such as
  `.speakerops/`.
- Added OpenAI config helpers:
  - `speakerops config --use-openai`
  - `speakerops config --model-provider`
  - `speakerops config --model`
  - `speakerops config --test-api`
- Made `api.key` lookup project-root based.
- Made chat more conversational and less likely to generate pages of text from
  a rough topic.
- Added a `Thinking...` status while waiting for model responses.
- Added chat artefact commands:
  - `/research`
  - `/cfp`
  - `/outline`
  - `/review`
  - `/help`
- Added `USERGUIDE.md`.
- Added a coloured ASCII SpeakerOps banner to help, init, and config.
- Added an Oh My Posh-style chat prompt showing the app, talk slug, and talk
  status.

**Why it mattered**

The CLI became usable as a guided tool rather than a set of disconnected
commands. The safety controls were already present, but this stage made the
workflow smoother and reduced user error.

**Safety posture**

Still local and single-user, but now easier to operate correctly. Chat artefact
commands remain explicit slash commands, not model-selected tools.

**Talk angle**

This stage is about developer experience as a safety feature. Better defaults,
clearer prompts, current context, and explicit commands make safer use more
likely.

## `v1.2-hardened-controls` - Hardened controls

**Commit:** `82a179a` - `Add hardened safety controls`

This stage added a dedicated local security policy layer for generated artefact
writes.

**What changed**

- Added `speakerops.security`.
- Added profile-driven security settings:

  ```yaml
  security:
    hardened: true
    allowed_operators: []
    scan_generated_content: true
    provenance_enabled: true
  ```

- Added local operator authorization:
  - Uses `SPEAKEROPS_OPERATOR` when set.
  - Otherwise uses the local operating-system username.
  - `allowed_operators` can restrict who can perform talk operations.
- Added generated-content secret scanning before previews are written.
- Blocks likely secrets such as:
  - OpenAI-style API keys.
  - GitHub tokens.
  - Private key blocks.
  - Generic `api_key`, `token`, `secret`, or `password` assignments.
  - High-entropy secret-like values.
- Added provenance records for approved generated artefacts.
- Writes `provenance.yaml` in each talk workspace.
- Provenance records include:
  - Timestamp.
  - Operator.
  - Action.
  - Target artefact.
  - Generated content hash.
  - Input file hashes.
- Moved audit logging onto the project root `.speakerops/audit.log` path for
  talk actions.
- Updated `speakerops config` to show:
  - Security hardened.
  - Secret scanning.
  - Provenance.
  - Allowed operators.
- Updated README, user guide, Copilot instructions, and project metadata to
  describe SpeakerOps as an early safety-focused MVP rather than an unsafe MVP.

**Why it mattered**

This stage made the generated-write path substantially more defensible. A
generated artefact now has to pass secret scanning, survive preview review, and
then receives a provenance record after approval.

**Safety posture**

SpeakerOps is now better described as an early safety-focused local agent CLI.
It is still not a hardened multi-user platform or sandboxed runtime, but it has
practical local controls around capability boundaries, content trust, network
use, generated writes, operator policy, and provenance.

**Talk angle**

This is the "hardened local agent workflow" stage. It shows how several small,
boring controls combine:

1. Scope the workspace.
2. Allowlist capabilities.
3. Deny sensitive paths.
4. Control network access.
5. Wrap untrusted content.
6. Review generated changes before applying.
7. Scan generated output for secrets.
8. Record provenance after approval.

## Overall evolution

SpeakerOps moved through three broad phases.

### Phase 1: Make the workflow real

`v0.1` proved that a local CLI could create and evolve talk artefacts from
files, prompts, and model output. It was intentionally unsafe because the
purpose was to discover the workflow.

### Phase 2: Add bounded controls

`v0.2` through `v1.0` added the key safety primitives:

- Workspace boundaries.
- Audit logging.
- Approval gates.
- Tool allowlisting.
- Network allowlisting.
- Sensitive path denylisting.
- Review-before-write.
- Prompt-injection content wrapping.
- Trust classification.

Each control is intentionally small and explainable. That makes the project a
good teaching vehicle: the controls are visible in code and visible in the CLI.

### Phase 3: Make it usable and harder to misuse

`v1.1` and `v1.2` focused on usability and stronger local hardening:

- Current-talk defaults.
- Better setup/configuration commands.
- Explicit chat slash commands for artefact generation.
- Better interactive feedback.
- User guide documentation.
- Operator policy.
- Secret scanning.
- Provenance records.

This is the practical message for the talk: security is not only about adding
barriers. It is also about shaping the workflow so the safe path is the easy
path.

## Suggested talk narrative

1. **Start with the useful but unsafe MVP.** Show why the workflow was worth
   building before discussing controls.
2. **Introduce each safety stage as a response to a concrete risk.** For
   example, path traversal led to workspace boundaries; unreviewed generated
   writes led to previews and diffs; untrusted web results led to content
   wrapping.
3. **Show the CLI as the demo object.** Run `speakerops chat`, generate a CFP
   through `/cfp`, inspect the preview, approve it, then show `provenance.yaml`.
4. **Emphasize boring controls.** The strongest controls here are not exotic:
   files, allowlists, audit logs, diffs, explicit commands, and hashes.
5. **Be honest about limits.** SpeakerOps is not a sandboxed, multi-user agent
   platform. It is a local safety-focused CLI that demonstrates the stages of
   making agentic workflows more governable.

## Remaining hardening opportunities

These are not yet implemented and are useful as "future work" in the talk:

- OS-level sandboxing or containerized execution.
- Strong identity integration beyond local username or `SPEAKEROPS_OPERATOR`.
- Cryptographic signing of provenance records.
- A richer policy engine for actions, artefacts, and model/provider behavior.
- Automated tests for security controls.
- Secret scanning of existing workspace files, not only generated content.
- Richer source provenance for web results.
- GitHub integration for pull-request based review.
- Multi-user workflows and role-based approval.
- Structured JSON audit logs with correlation IDs.
