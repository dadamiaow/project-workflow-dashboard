---
name: project-workflow-dashboard
description: Create or refresh a project workflow dashboard from existing progress records, reports, or metrics. Use when a project needs a reusable README entry, a browser-readable offline HTML overview, or selected milestone snapshots.
---

# Project workflow dashboard

1. Find the project's maintained progress entry, latest applicable result, and any existing dashboard generator. Reuse those sources and the established locations. Verify the report version and related inputs when hashes or IDs are available. If a stage is unverified or a run is stale, label it accordingly. Keep source data and scoring logic in the project.
2. Use same-page tabs that switch visible panels. Start with Progress, Key results, and Details and sources when the content supports them. Rename, omit, or add panels to fit the project. For a single view, show it directly. Put a prominent Current step card on Progress with its actual status, immediate next action, and any blocker. Mark approved work that has yet to start as pending. Add a short Experiments and learning section when there is something to record. Capture the question, why the comparison was run, the finding, and the useful follow-up or reference. Keep detailed evidence in the source records.
3. Make detailed groups easy to distinguish when open. Give first-level disclosures their own borders and distinct open headers. Indent child disclosures and use a vertical guide to show their parent. Keep chart and table values traceable with units, comparison scope, and a portable locator such as a repo-relative path or run ID. Keep credentials, private source content, and reference answers out of exports unless the user explicitly requires them and the destination is appropriate.
4. If the project already has a usable generator, prefer its normal entry point. Otherwise map existing sources to the small JSON input below and run the bundled renderer. To make future updates reproducible, reuse an existing project data export or keep a minimal project-owned adapter when the mapping is recurring. Treat the generated HTML as an output, so refreshes come from current source data.
5. When asked to keep the dashboard in a project, link the stable output from its existing README. Default to `docs/workflow.html` when there is already a `docs/` directory, otherwise `workflow.html`. Confirm the linked file exists. Open the result in the Codex panel when requested and available, and provide the file path for offline viewing.
6. A routine refresh only updates the current HTML. For an explicitly selected milestone or baseline, also save one dated HTML in the project's archive, for example `docs/archive/workflow/2026-11-24-release-baseline.html`. Identical snapshot content is kept once and an existing snapshot is never replaced. Verify the source values, current step, tab switching and foldout hierarchy, and any saved archive after rendering.

## Renderer

Use Python 3.10+ with the bundled [scripts/render.py](scripts/render.py). Paths relative to the working directory refer to the project. The template is loaded relative to the script.

```sh
python /path/to/project-workflow-dashboard/scripts/render.py data.json --output docs/workflow.html
# For a selected milestone, append:
# --snapshot docs/archive/workflow/2026-11-24-release-baseline.html
```

Example JSON input:

```json
{
  "title": "Release workflow",
  "as_of": "2026-11-24",
  "summary": "Staging approved. Production rollout is next.",
  "current_step": {"title": "Production rollout", "status": "Pending", "next_action": "Schedule the rollout window."},
  "stages": [
    {"title": "Tests", "status": "Passed", "detail": "118 / 120 checks passed."},
    {"title": "Production rollout", "status": "Pending"}
  ]
}
```

Optional top-level fields:

- `lang`: HTML language tag. Defaults to `en`. Use `zh-CN` for Chinese interface labels.
- `labels`: display overrides for `progress`, `results`, `details`, `current_step`, `learning`, and `sources`. The renderer shows tabs only for populated panels. Use the project's generator or template for additional panels.
- `current_step`: object with `title`, `status`, and optional `detail` and `next_action`. Take the values from the maintained progress record.
- `learning`: short records with `title` and optional `question`, `comparison`, `result`, `next_step`, and `sources`. Use `comparison` for the methods and rationale, and link the full record or reference from `sources`.
- `charts`: one or more objects with `title`, positive `max`, optional `unit` (for example `%`), and `values` as rows such as `[["Current", 98.3], ["Previous", 95.0]]`. Chart values use display units and range from zero to `max`.
- `tables`: objects with `title`, string `columns`, and `rows` of matching width. Cells accept strings, numbers, and null for unavailable values.
- `details`: objects with `title` and optional `text`, `tables`, and `children`. Children use the same detail shape and display as indented disclosures.
- `sources`: strings identifying the input files, versions, dates, or run IDs. Use paths relative to the project and identifiers that still make sense when reading an offline copy.

Statuses use the project's terms and the stage order is the main reading order. Use `detail` to mark actual parallel work, dependencies, or blockers. Map chart values and exact table values from the same report. The renderer validates input, escapes text, and uses a self-contained local HTML template.
