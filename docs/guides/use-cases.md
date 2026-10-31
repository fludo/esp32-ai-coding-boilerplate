# Use Cases and Commands

Start with the [Quick Start](./quickstart.md) if the project is not configured yet. This page maps common development outcomes to the command that owns them.

## Set the workflow mode

Normal Mode runs the full verification flow. To save Lite Mode as this project's default, run:

```bash
python3 scripts/set_workflow_mode.py lite
```

The script adds `Workflow Mode: Lite.` to `CLAUDE.md`. Future workflow sessions use it without a spoken mode selection. Run the same command with `normal` to remove the saved directive; other project rules are preserved. An explicit mode selection in the conversation takes precedence over the saved default.

Lite Mode omits independent code verification, design synchronization, and the security-reviewer call. For a Work Plan task set it replaces per-task quality-fixer runs with one final run before code review. Focused implementation checks, required integration/on-target/system test review, document approval, Small's quality run, and post-review quality checks remain applicable. Completion reports identify omitted or unavailable proof.

## Choose a command

### Implementation and investigation

| Command | Outcome |
|---|---|
| `/implement <request>` | Confirm requirements and complete the applicable design, implementation, verification, and commit flow |
| `/task <request>` | Execute one focused task after identifying its scope and applicable skills |
| `/diagnose <problem>` | Investigate a problem, independently verify the cause, and derive supported solutions without implementing one |
| `/review [Design Doc]` | Review completed implementation against the agreed outcome, repository standards, and security boundaries, then apply user-approved corrections |

### Design and planned execution

| Command | Outcome |
|---|---|
| `/design <request>` | Confirm scope, resolve qualifying ADR decisions, and produce an approved Design Doc |
| `/plan [Design Doc]` | Create, review, and approve a Work Plan; optionally generate integration/on-target/system test skeletons first |
| `/build [Work Plan]` | Materialize and execute task files from approved planned work |
| `/add-integration-tests [Design Doc]` | Add the smallest integration/on-target/system test set needed to prove accepted behavior in existing code |
| `/reverse-engineer <path>` | Discover existing behavior and generate reviewed PRDs and optional Design Docs |
| `/update-doc [document]` | Update and review an existing PRD, ADR, or Design Doc without continuing into implementation |

### Project knowledge and skills

| Command | Outcome |
|---|---|
| `/project-inject` | Record project-specific prerequisites and quality standards in `project-context` |
| `/create-skill <knowledge>` | Create a new skill through an interactive hearing and review |
| `/refine-skill <change>` | Apply a targeted change to an existing skill and review the result |

## Common flows

### Complete a change

```text
/implement Publish meter readings to MQTT every 10 s with reconnect
```

Use `/implement` when one request should proceed through its complete lifecycle. It confirms the outcome and exclusions first, then chooses the smallest document and implementation route supported by repository evidence.

### Execute a focused task

```text
/task Fix the DSMR parser for negative export values
```

Use `/task` when the request already has one focused outcome and does not need the full design-to-build workflow.

### Diagnose before choosing a fix

Paste the serial log (from the reset line to the failure) with the request; the `esp32-debugging` skill routes crashes, watchdog resets, and build/upload failures to the matching playbook.

```text
/diagnose Device reboots with Task watchdog got triggered after ~2 hours
```

`/diagnose` reports verified causes and supported solution options. Give a separate implementation instruction after choosing a solution.

### Separate design, planning, and implementation

```text
/design Add OTA updates over HTTPS
/plan docs/design/ota-update-design.md
/build docs/plans/20261031-feature-ota-update.md
```

Use the separate commands when each durable artifact should be approved before continuing or when planned work will be executed in another session.

### Resume existing planned work

```text
/build
```

With no argument, `/build` resolves the consumable task set owned by that recipe. Pass the Work Plan path when more than one plan could be intended.

### Review completed implementation

```text
/review docs/design/ota-update-design.md
```

The command checks whether the completed implementation meets the agreed outcome and repository standards, contains no unnecessary changes, and has no serious functional, reliability, or security issues. It presents supported findings, applies only the corrections you approve, rechecks those findings after correction, and runs the quality check once the review converges. It does not create task files for review fixes.

## Document routing

| Structural Scale | Condition | Durable artifacts |
|---|---|---|
| Small | One coherent outcome has one evident repository-supported implementation inside one responsibility boundary | None |
| Medium | One coherent outcome coordinates a boundary or contains a potentially durable choice | Design Doc → Work Plan |
| Large | Multiple independently valuable outcomes require separate design decisions | PRD → Design Doc → Work Plan |

File count is evidence about the change surface, not the scale rule.

- A technical topic produces an ADR only when at least two credible materially different choices remain and the choice has durable impact. The ADR batch is approved before the Design Doc.
- Small work passes its confirmed outcome, governing sources, affected paths, and observable verification directly to implementation. It does not create placeholder documents or task files.

## Test and quality behavior

- Tests run host-first: `pio test -e native` for `lib/` logic, then on-target (`pio test -e <board>`) and system tests only where hardware or a live peer is the proof boundary. Skeletons are selected from accepted behavior and proof obligations. Existing tests count only when they exercise the same boundary and fail for the material failure being covered.
- One scenario may prove several obligations when its assertions keep the failure mapping clear. Different setup or failure modes remain separate.
- `quality-fixer` runs `scripts/check.sh` (clang-format, `pio check` with `--fail-on-defect`, native tests, builds for every board environment) plus task verification methods, fixes failures owned by the change, and records unavailable checks or unrelated baseline failures.
- A quality result does not claim that an unavailable check passed — on-target tests without an attached board are reported as blocked. Build and review completion reports preserve that limitation.

## Artifact lifecycle

- PRDs, ADRs, and Design Docs are durable governing sources.
- Work Plans hold approved implementation order and task boundaries.
- Materialized task files are execution handoffs. Build recipes delete the task files they consume after the corresponding work is committed.

## Customizing project behavior

Use `/project-inject` for facts, constraints, and quality standards that apply to this repository. Use a skill for reusable judgment that should load only for a particular responsibility. Do not copy feature-specific decisions into a global rule; keep them in the applicable PRD, ADR, or Design Doc.

See the [Skills Editing Guide](./skills-editing-guide.md) for placement and validation guidance.

The command definitions under `.claude/commands/` are the source of truth for detailed execution behavior.
