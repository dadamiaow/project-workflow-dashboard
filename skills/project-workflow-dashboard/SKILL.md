---
name: project-workflow-dashboard
description: Create or refresh a project workflow dashboard from existing progress records, reports, or metrics. Use when a project needs a reusable README entry, a browser-readable offline HTML overview, or selected milestone snapshots.
---

# Project workflow dashboard

1. Find the project's maintained progress entry, latest applicable result, and any existing dashboard generator. Reuse those sources and the established locations. Map metric values directly from machine-readable project reports where available. Verify report versions and related inputs when hashes or IDs are available. Use `null` for missing table values and label missing, stale, or unverified data and stages as applicable. Keep source data and scoring logic in the project.
2. Use same-page tabs that switch visible panels. Start with Progress, Key results, and Details and sources when the content supports them. Rename, omit, or add panels to fit the project. For a single view, show it directly. Put a prominent Current step card on Progress with its actual status, immediate next action, and any blocker. Mark approved work that has yet to start as pending. When there's an experiment to record, add a short Experiments and learning section. State the question, the change and fixed conditions, the observed outcome, any limits on interpretation such as shared context across questions, and one concrete verification action. Cite specific samples when they help explain the outcome. Check attribution hypotheses against the source reports and evidence before presenting them as findings. Keep detailed evidence in the source records.
3. Make detailed groups easy to distinguish when open. Give first-level disclosures their own borders and distinct open headers. Indent child disclosures and use a vertical guide to show their parent. Keep chart and table values traceable with units, comparison scope, and a portable locator such as a repo-relative path, in-page anchor, or run ID. When per-sample reports are available and examples help explain the result, include a few diagnostic samples in `details` with the sample ID, observed issue, verification status, and report locator. Check display text and locators for sensitive content before rendering or archiving. Exclude credentials. Include private source content or reference answers only when explicitly requested and appropriate for the destination.
4. If the project already has a usable generator, prefer its normal entry point. Otherwise map existing sources to the small JSON input below and run the bundled renderer. Verify that the output includes the selected run and any requested learning record. If the generator cannot display a requested record, use a compatible rendering path or report the missing output. For a comparison, record the baseline and current run IDs or report paths, what changed, the dataset version, sample count, and metric definition. Show deltas only after verifying the same evaluation samples, metric definition, and scoring protocol. Use report metadata, sample IDs, or matching evaluation-input hashes as available. If comparability cannot be verified, label the known differences or missing metadata and present each run's results without deltas. For a chunking comparison, keep questions and source evidence anchors fixed, remap nodes for each version, and record the remapping. To make future updates reproducible, reuse an existing project data export or keep a minimal project-owned adapter when the mapping is recurring. Treat the generated HTML as an output, so refreshes come from current source data.
5. When asked to keep the dashboard in a project, link the stable output from its existing README. Default to `docs/workflow.html` when there is already a `docs/` directory, otherwise `workflow.html`. Confirm the linked file exists. Open the result in the Codex panel when requested and available, and provide the file path for offline viewing.
6. Save requested progress or learning updates in the project's maintained records before rendering. A routine refresh regenerates the current HTML from those records and reports. For an explicitly selected milestone or baseline, also save one dated HTML in the project's archive, for example `docs/archive/workflow/2026-11-24-release-baseline.html`. Identical snapshot content is kept once and an existing snapshot is never replaced. Verify the source values, current step, tab switching and foldout hierarchy, and any saved archive after rendering.

## Renderer

Use Python 3.10+ with the bundled [scripts/render.py](scripts/render.py). Paths relative to the working directory refer to the project. The template is loaded relative to the script.

```sh
python /path/to/project-workflow-dashboard/scripts/render.py data.json --output docs/workflow.html
# For a selected milestone, append:
# --snapshot docs/archive/workflow/2026-11-24-release-baseline.html
```

The bundled renderer requires nonempty text for `title`, `as_of`, and `summary`, and a nonempty `stages` list. Each stage requires nonempty `title` and `status` strings. Omit unavailable optional text fields. Use `null` for unavailable table cells and label the reason in adjacent text or a status column. Omit unavailable chart points and omit the chart if no points remain.

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
- `learning`: short records with `title` and optional `question`, `comparison`, `result`, `next_step`, and `sources`. Use `comparison` for the change and fixed conditions and `result` for observations. Record experimental limits where they apply. Use `sources` for a traceable repo-relative path, run ID, or in-page anchor.
- `charts`: one or more objects with `title`, positive `max`, optional `unit` (for example `%`), and `values` as rows such as `[["Current", 98.3], ["Previous", 95.0]]`. Chart values use display units and range from zero to `max`.
- `tables`: objects with `title`, string `columns`, and `rows` of matching width. Cells accept strings, numbers, and null for unavailable values.
- `details`: objects with `title` and optional `text`, `tables`, and `children`. Children use the same detail shape and display as indented disclosures. With the bundled renderer, put sample locators in `text` or table cells. Top-level and `learning.sources` entries display as plain text. Use an in-page anchor only when the generator emits the target.
- `sources`: strings identifying the input files, versions, dates, or run IDs. Use paths relative to the project and identifiers that still make sense when reading an offline copy.

Statuses use the project's terms and the stage order is the main reading order. Use `detail` to mark actual parallel work, dependencies, or blockers. For each run and metric shown in both a chart and a table, use the same source value and unit conversion. The renderer validates input, escapes text, and uses a self-contained local HTML template.
